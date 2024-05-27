import {useState,useEffect} from 'react';
import RefreshIcon from '@mui/icons-material/Refresh';
import Button from '@mui/material/Button';

import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-pgsql";
import "ace-builds/src-noconflict/theme-eclipse";
import "ace-builds/src-noconflict/ext-language_tools";

import FeedbackInput from './FeedbackInput.js';
import {LoadingDisplay} from './Utils.js';


function EditorBox(props)
{
	const {sqlquery,enabled,onsqlchange,...other} = props;
	return (<AceEditor mode="pgsql" onChange={(val)=>{;}} theme="eclipse" name="sqleditorbox" showGutter={false} fontSize={24}
					   editorProps={{$blockScrolling:true,$enableAutoIndent:true}} setOptions={{showLineNumbers:false}} onChange={()=>{onsqlchange(ace.edit("sqleditorbox").getValue());}} 
					   value={sqlquery} style={{width:"100%",height:"300px"}} readOnly={!enabled} highlightActiveLine={enabled} />);
}

function TranslationMetrics(props)
{
	const {executiontime,numtokens,...other} = props;
	return (executiontime!==-1||numtokens!==-1?(<div className="flexcenter" style={{marginRight:"20px",marginTop:"10px"}}>
			 								        <pre>{(executiontime!==-1?("Execution time: "+executiontime.toFixed(4)+"s\n"):"")+((numtokens!==-1?("Token count: "+numtokens):""))}</pre>
												</div>):"");
}

function SQLReloadButton(props)
{
	const {enabled,onsubmitsql,...other} = props;
	return (<Button style={{marginTop:"10px",marginLeft:"10px"}} disabled={!enabled} variant="contained" size="large"
					onClick={()=>{onsubmitsql(ace.edit("sqleditorbox").getValue());}} endIcon={<RefreshIcon />}>Reload Query</Button>);
}

function QueryTranslator(props)
{
	const {show,api,sessionid,enabled,loading,stoploading,nlquery,table,queryid,translationmode,sqlquery,onsqlquerychange,executiontime,numtokens,onsubmitsql,...other} = props;
	const [feedbackmode,setfeedbackmode] = useState(-1);
	
	let feedback = {query:nlquery,table:table,value:sqlquery,query_id:queryid,system:translationmode,sessionid:sessionid};
	
	useEffect(()=>{setfeedbackmode(0);},[loading]);
	useEffect(()=>{setfeedbackmode(-1);},[nlquery]);
	
	function changesql(sql)
	{
		if(feedbackmode != 2)
			setfeedbackmode(-1);
		onsqlquerychange(sql);
	}
	
	return (!show?<LoadingDisplay show={loading} message="Translating query" abort={stoploading} />
				 :<>
				      <EditorBox sqlquery={sqlquery} onsqlchange={changesql} enabled={enabled} feedbackmode={feedbackmode} setfeedbackmode={setfeedbackmode} />
					  <div className="flexright">
					      <TranslationMetrics executiontime={executiontime} numtokens={numtokens} />
						  <FeedbackInput enabled={enabled} type="translation" api={api} mode={feedbackmode} setmode={setfeedbackmode} feedback={feedback} />
						  <SQLReloadButton enabled={enabled} onsubmitsql={onsubmitsql} />
					  </div>
				  </>);
}


export default QueryTranslator;