import './App.css';
import {useState} from 'react';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Button from '@mui/material/Button';

import {APIRequester} from './base.js';
import {FatalError,LayoutTable,LoadingDisplay} from './Utils.js';
import InputArea from './InputArea.js';
import QueryTranslator from './QueryTranslator.js';
import IntentDetector from './IntentDetector.js';
import {NLExplanation,ResultsTable} from './QueryResults.js';
import LoginControl from './LoginControl.js';

function App()
{
	const [stage,setstage] = useState(0);
	const [promode,setpromode] = useState(0);
    const [translationmode,settranslationmode] = useState("llama7b");
	const [nlquery,setnlquery] = useState("");
	const [sqlquery,setsqlquery] = useState("");
	const [explanation,setexplanation] = useState("");
	const [executiontime,setexecutiontime] = useState(-1);
	const [numtokens,setnumtokens] = useState(-1);
	const [selectedtable,setselectedtable] = useState("");
	const [tablelist,settablelist] = useState([]);
	const [queryresult,setqueryresult] = useState({"status":"EMPTY","message":"","columnnames":[],"rows":[]});
	const [loadingquery,setloadingquery] = useState(false);
	const [loadingresults,setloadingresults] = useState(false);
	const [devmode,setdevmode] = useState(false);
	const [fatalerror,setfatalerror] = useState(false);
	const [loggedin,setloggedin] = useState(false);
	const [expired,setexpired] = useState(false);
	const [queryid,setqueryid] = useState("");
	const [aborter,setaborter] = useState(undefined);
	const [api,setapi] = useState(()=>(new APIRequester(delog)));
	const [sessionid,setsessionid] = useState("");
		
	function changetable(table) { setselectedtable(table); setloadingquery(true); getnltosql(tablelist,table,nlquery,false); setstage(1); }
		
	function switchpromode(pmd) { settranslationmode(pmd?"llama7b":"chatgpt"); setpromode(!pmd); setstage(0); }
		
	async function processquery(query)
	{
		if(loadingquery || loadingresults)
			return;
		setstage(0);
		setfatalerror(false);
		setqueryid("");
		if(query !== "")
		{
			setloadingquery(true);
			console.log("Processing query...");
			console.log("Getting table list...");
			await api.request("tableintent",{query:query,sessionid:sessionid},
							  (data)=>{tableset(data["tables"],query);},
							  "Error retrieving table list.",
							  (e)=>{setloadingquery(false);settablelist([]);setstage(0);setfatalerror(true);});
		}
		else
		{
			console.log("Error: empty query.");
			setloadingquery(false);
		}
	}
	
	function tableset(tables,query)
	{
		settablelist(tables.sort((a,b)=>(b["score"]>a["score"]?1:(b["score"]<a["score"]?-1:0))));
		if(tables.length > 0)
		{
			console.log("Got table list:");
			console.log(tables);
			setselectedtable(tables[0]["name"]);
			getnltosql(tables,tables[0]["name"],query,true);
		}
		else
		{
			settablelist([]);
			setselectedtable("");
		}
		setstage(1);
	}
	
	async function getnltosql(tables,seltable,nlq,pipelined)
	{
		if(!pipelined && (loadingquery || loadingresults))
			return;
		if(tables.length > 0 && seltable !== "" && nlq !== "")
		{
			console.log("Translating NL to SQL...");
			await api.request("nltosql",{query:nlq,table:seltable,system:translationmode,sessionid:sessionid},
					          (data)=>{sqlset(data.sql,data.query_id,data.explanation,data.execution_time,data.token_count,data.status_code,data.message,nlq,seltable);},
							  "Error fetching NL to SQL result.",
					          (e)=>{sqlset("","","",-1,-1,500,""+e,nlq,seltable);});
		}
		setloadingquery(false);
	}
	
	function sqlset(sqlstr,queryid,expl,exectime,toknum,code,message,nlq,seltable)
	{
		setstage(2);
		setsqlquery(sqlstr);
		setqueryid(queryid);
		setexplanation(expl);
		setexecutiontime(exectime);
		setnumtokens(toknum);
		console.log("Translation request returned status code: "+code);
		if(sqlstr !== "")
		{
			if(code !== 200)
			{
				console.log("Error fetching SQL translation: "+message+" (Code "+code+")");
				getresultstable(sqlstr,"Error fetching SQL translation: "+message+" (Code "+code+")",false);
			}
			else
			{
				console.log("Got NL to SQL translation: \""+nlq+"\" (Table: "+seltable+") -> "+sqlstr);
				getresultstable(sqlstr,"",false);
			}
		}
		else
		{
			console.log("No NL to SQL translation available.");
			setsqlquery("---"+translationmode+" did not return an SQL query");
			resulttableset({"status":"EMPTY","message":"","columnnames":[],"rows":[]});
		}
	}
	function delog(logout)
	{
		setstage(0);
		setpromode(1);
		setnlquery("");
		setsqlquery("");
		setexplanation("");
		setexecutiontime(-1);
		setnumtokens(-1);
		setselectedtable("");
		settablelist([]);
		setqueryresult({"status":"EMPTY","message":"","columnnames":[],"rows":[]});
		setloadingquery(false);
		setloadingresults(false);
		setfatalerror(false);
		setexpired(logout?false:true);
		setloggedin(false);
		setqueryid("");
		setsessionid("");
	}
	
	async function logout()
	{
		await api.request("logout",{sessionid:sessionid},()=>delog(true),"Error logging out.",()=>delog(false));
	}
	
	async function getresultstable(sqlstr,err,fromreload)
	{
		setloadingresults(true);
		setstage(2);
		if(fromreload)
		{
			setexplanation("");
			setexecutiontime(-1);
			setnumtokens(-1);
		}
		console.log("Getting SQL query results...");
		console.log("Query: "+sqlstr);
		setsqlquery(sqlstr);
		if(err !== null && err !== "")
		{
			resulttableset({"status":"ERROR","message":err,"columnnames":[],"rows":[]});
			setloadingresults(false);
			return;
		}
		await api.request("sqlresults",{query:sqlstr,sessionid:sessionid},
				          (data)=>{resulttableset(data);},
					 	  "Error fetching SQL results.",
				          (e)=>{resulttableset({"status":"ERROR","message":e.message,"columnnames":[],"rows":[]});});
		setloadingresults(false);
	}
	
	function resulttableset(data)
	{
		setstage(3);
		setqueryresult(data);
		console.log("Got SQL query results.");
		console.log(data);
	}
	
	function stoptranslate()
	{
		console.log("Stopping NL to SQL translation...");
		api.abort();
		setstage(2);
		sqlset("","","",-1,-1,500,"Translation Aborted.",nlquery,selectedtable);
		setloadingquery(false);
	}
	
	function stopresults()
	{
		console.log("Stopping SQL query execution...");
		api.abort();
		setstage(2);
		resulttableset({"status":"ERROR","message":"Operation Aborted.","columnnames":[],"rows":[]});
		setloadingresults(false);
	}
	
	let inputarea = <InputArea enabled={!loadingquery&&!loadingresults} devmode={devmode} query={nlquery} onquerychange={setnlquery} onsubmitquery={processquery}
			                   translationmode={translationmode} onmodechange={settranslationmode} promode={promode} />;
	let intentdetector = <IntentDetector show={stage>=1} enabled={!loadingquery&&!loadingresults} api={api} sessionid={sessionid}
										 query={nlquery} tables={tablelist} selectedtable={selectedtable} ontablechange={changetable} />;
	let querytranslator = <QueryTranslator show={stage>=2} api={api} sessionid={sessionid} loading={loadingquery} stoploading={stoptranslate}
										   sqlquery={sqlquery} onsqlquerychange={setsqlquery} enabled={!loadingquery&&!loadingresults}
										   executiontime={executiontime} numtokens={numtokens} translationmode={translationmode}
										   onsubmitsql={(sql)=>{getresultstable(sql,null,true);}} />;
	let devarea = <Collapse in={devmode}>
					  <LayoutTable style={{width:"100%"}} rows={[[{content:intentdetector,width:"50%"},
																  {content:querytranslator,width:"50%"}]]} />
				  </Collapse>;
	let nlexplanation = <NLExplanation show={explanation!==""&&stage>=2} explanation={explanation} />;
	let loadingdisplay = <LoadingDisplay show={stage<3&&(loadingresults||(loadingquery&&!devmode))} message={(devmode||!loadingquery)?"Loading results":"Translating query"}
									     abort={()=>{(devmode||!loadingquery)?stopresults():stoptranslate();}} />;
	let resultstable = <ResultsTable st={queryresult["status"]} message={queryresult["message"]} colnames={queryresult["columnnames"]} rows={queryresult["rows"]} />;
	let logo = <div className="flexcenter"><h1><span id="statbot">Statbot</span><span id="swiss">.SWISS</span></h1></div>;
	
	let maincontent =  <LayoutTable style={{width:"100%"}} rows={[[{content:logo}],
																  [{content:inputarea}],
			                                                      [{content:fatalerror?<FatalError />:""}],
																  [{content:devarea}],
																  [{content:nlexplanation}],
								                                  [{content:stage<3?loadingdisplay:resultstable}]]} />;
																  
	let devmodeswitch = <div id="devmodeswitch" style={{backgroundColor:"#e2e7e9",paddingRight:"15px",borderRadius:"20px"}}>
							<FormControlLabel labelPlacement={"start"} label={"Expert Mode"} control={<Checkbox onChange={(e)=>{setdevmode(!devmode);}} checked={devmode} />} />
						</div>;
	let logoutbutton = <div id="logoutbutton"><Button variant="outlined" onClick={()=>logout()}>Log Out</Button></div>;
	let promodebutton = <div id="promodebutton"><Button variant="contained" onClick={()=>switchpromode(0)}>Use Pro Version</Button></div>;
	
    return (<div className="flexcenter" style={{paddingTop:"5%",paddingLeft:"5%",paddingRight:"5%"}}>
				{((loggedin||!promode)?<><div className="flexcenter" style={{width:"100%"}}>{maincontent}</div>{devmodeswitch}{promode?logoutbutton:""}{!promode?promodebutton:""}</>
					                  :<LoginControl api={api} onlogin={setsessionid} loginset={setloggedin} expired={expired} setexpired={setexpired} tofreemode={()=>switchpromode(1)} />)}
			</div>);
}

export default App;
