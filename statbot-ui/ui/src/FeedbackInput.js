import './FeedbackInput.css';
import {useState,useEffect} from 'react';
import Button from '@mui/material/Button';
import CheckIcon from '@mui/icons-material/Check';
import ClearIcon from '@mui/icons-material/Clear';

function SetButton(props)
{
	const {children,set,...other} = props;
	return (<Button variant={set?"contained":"outlined"} size="large" style={{marginTop:"10px",marginLeft:"10px"}} {...other}>{children}</Button>);
}

function FeedbackInput(props)
{
	const {mode,setmode,enabled,api,type,feedback,...other} = props;
	
	async function sendfeedback(correct)
	{
		await api.request(type+"feedback",{correct:correct,...feedback},
		                 (data)=>{console.log(type+"Feedback ("+(correct?"":"in")+"correct): ",data);},
						 "Error sending "+type+" feedback.",
				         ()=>{});
		setmode(correct?1:2);
	}
	async function sendcorrection()
	{
		await api.request(type+"corrections",feedback,
		                  (data)=>{console.log(type+"Correction: ",data);},
				          "Error sending "+type+" correction.",
				          ()=>{});
		setmode(3);
	}
	return (<>
				<SetButton set={mode===1} disabled={mode!==0||!enabled} onClick={()=>{sendfeedback(true);}}><CheckIcon /></SetButton>
				<SetButton set={mode===2||mode===3} disabled={mode!==0||!enabled} onClick={()=>{sendfeedback(false);}}><ClearIcon /></SetButton>
				<SetButton set={mode===3} disabled={mode!==2||!enabled} onClick={()=>{sendcorrection();}}>Submit Correction</SetButton>
			</>);
}

export default FeedbackInput;
