import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import EastIcon from '@mui/icons-material/East';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import {LayoutTable} from './Utils.js';

function InputArea(props)
{
	const {devmode,enabled,query,onquerychange,translationmode,onmodechange,onsubmitquery,promode,...other} = props;
	return (<LayoutTable rows={[[{content:<TextField autoFocus onKeyPress={(e)=>{if((e.key==="Enter"||e.key==="NumpadEnter")&&enabled){onsubmitquery(e.target.value);}}} style={{"width":"100%"}}
													 onChange={(e)=>{onquerychange(e.target.value);}} placeholder="Enter a natural language query"></TextField>,width:devmode&&promode?"85%":"95%"},
		                         {content:devmode&&promode?<SystemSelector set={onmodechange} val={translationmode} enabled={enabled} />:"",width:devmode&&promode?"10%":"0%"},
							     {content:<Button style={{width:"100%"}} size="large" variant="contained" onClick={()=>onsubmitquery(query)} disabled={!enabled}><EastIcon /></Button>,width:"5%"}]]} />);
}

function SystemSelector(props)
{
	const {set,val,enabled,...other} = props;
	return (<ToggleButtonGroup exclusive value={val} onChange={(e,v)=>{if(v!==null)set(v);}} style={{width:"100%"}}>
				<ToggleButton disabled={(!enabled)&&(val!=="chatgpt")} value={"chatgpt"} style={{"textTransform":"none","paddingLeft":"20px","paddingRight":"20px"}}>ChatGPT</ToggleButton>
				<ToggleButton disabled={(!enabled)&&(val!=="llama7b")} value={"llama7b"} style={{"textTransform":"none","paddingLeft":"20px","paddingRight":"20px"}}>LLaMA-7b</ToggleButton>
			</ToggleButtonGroup>);
}

export default InputArea;