import './IntentDetector.css';
import {useState,useEffect} from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import FeedbackInput from './FeedbackInput.js';

function IntentDetector(props)
{	
	const {show,enabled,valid,api,sessionid,query,tables,selectedtable,ontablechange,...other} = props;
	const [feedbackmode,setfeedbackmode] = useState(-1);
	
	useEffect(()=>{setfeedbackmode(0);},[tables]);
	useEffect(()=>{setfeedbackmode(-1);},[query]);
	
	function changetable(table)
	{
		if(!enabled || table === null)
			return;
		if(feedbackmode === 0)
			setfeedbackmode(-1);
		ontablechange(table);
	}
	
	return (show?<>
			  	     <TableSelector set={changetable} val={selectedtable} tables={tables} enabled={enabled} style={{width:"100%"}} />
				     <div className="flexright">
						<FeedbackInput enabled={enabled} mode={feedbackmode} setmode={setfeedbackmode} api={api} type="intent" feedback={{query:query,method:"basic",value:selectedtable,sessionid:sessionid}} />
					 </div>
			      </>:"");
}

function TableSelector(props)
{
	const {set,tables,val,enabled,...other} = props;
	
	return (<div style={{overflowY:"auto",maxHeight:"400px",padding:"5px"}}>
				<ToggleButtonGroup exclusive value={val} onChange={(e,v)=>set(v)} orientation="vertical" style={{width:"100%"}}>
					{tables.map((table,i)=>(<ToggleButton disabled={!enabled&&table["name"]!==val} style={{"textTransform":"none","padding":"0px"}} key={""+i} value={table["name"]}>
												<span className="tabletext" style={{width:"90%",color:!enabled&&table["name"]!==val?"lightgray":"black"}}>{table["name"].replaceAll("_","_\u200b")}</span>
												<span className="tabletext" style={{color:!enabled&&table["name"]!==val?"lightgray":"black"}}>{table["score"].toFixed(4)}</span>
											</ToggleButton>))}
				</ToggleButtonGroup>
			</div>);
}

export default IntentDetector;
