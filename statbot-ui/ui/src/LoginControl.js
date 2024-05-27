import './LoginControl.css';
import {useState} from 'react';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import {LayoutTable} from './Utils.js';

function LoginInput(props)
{
	const {show,enabled,label,valset,send,...other} = props;
	return (show?<div className="flexcenter">
				     <TextField disabled={!enabled} onChange={(e)=>valset(e.target.value)} onKeyPress={(e)=>{if((e.key==="Enter"||e.key==="NumpadEnter")&&enabled)send();}} label={label} {...other}></TextField>
			     </div>:"");
}

function LoginControl(props)
{
	const {api,loginset,expired,setexpired,onlogin,tofreemode,...other} = props;
	const [signin,setsignin] = useState(true);
	const [errormessage,seterrormessage] = useState("");
	const [isloading,setisloading] = useState(false);
	const [username,setusername] = useState("");
	const [pass,setpass] = useState("");
	const [pass2,setpass2] = useState("");
	function ssetsignin(v) {if(v!==null)setsignin(v);};

	function handleloginresponse(data)
	{
		if(data.status==="ERROR" && data.error==="USER_DOES_NOT_EXIST")
			seterrormessage("Error: user does not exist.");
		else if(data.status==="ERROR" && data.error==="INVALID_PASSWORD")
			seterrormessage("Error: invalid password. Please contact "+process.env.REACT_APP_ADMIN_MAIL+" to request a password reset.");
		else if(data.status==="ERROR" && data.error==="ACCESS_DENIED")
			seterrormessage("Error: user does not have permission to access this page. Please contact "+process.env.REACT_APP_ADMIN_MAIL+" to request access.");
		else
		{
			onlogin(data.sessionid);
			loginset(true);
		}
		setisloading(false);
	}
	
	function handlecreateaccountresponse(data)
	{
		if(data.status==="ERROR" && data.error==="USER_ALREADY_EXISTS")
		{
			seterrormessage("Error: user already exists.");
			setisloading(false);
		}
		else
		{
			setsignin(true);
			sendlogin(true);
		}
	}
	
	async function sendlogin(rep)
	{
		setexpired(false);
		seterrormessage("");
		if(username === "")
		{
			seterrormessage("Error: username is empty.");
			return;
		}
		if(pass === "")
		{
			seterrormessage("Error: password is empty.");
			return;
		}
		if(!signin && pass !== pass2)
		{
			seterrormessage("Error: passwords do not match.");
			return;
		}
		setisloading(true);
		if(signin || rep)
		{
			api.request("login",{username:username,password:pass},
						handleloginresponse,
						"Error logging in.",
						()=>{seterrormessage("Error: could not connect to server.");setisloading(false);});
		}
		else
		{
			api.request("createaccount",{username:username,password:pass},
						handlecreateaccountresponse,
						"Error creating account.",
						()=>{seterrormessage("Error: could not connect to server.");setisloading(false);});
		}
	}
	
	let modeswitch = <div className="flexcenter">
						<ToggleButtonGroup exclusive value={signin} onChange={(e,v)=>{ssetsignin(v);seterrormessage("");}} style={{border:"0px",borderRadius:"20px"}}>
							<ToggleButton disabled={isloading} value={true} style={{border:"0px",borderBottom:(signin?"1":"0")+"px solid lightgray",borderRadius:"20px",marginRight:"10px"}}>{"Log In"}</ToggleButton>
							<ToggleButton disabled={isloading} value={false} style={{border:"0px",borderBottom:(signin?"0":"1")+"px solid lightgray",borderRadius:"20px"}}>{"Create Account"}</ToggleButton>
						</ToggleButtonGroup>
					 </div>;
	let namebox = <LoginInput show={true} enabled={!isloading} label="Username" valset={setusername} send={()=>{sendlogin(false);}} autoFocus />
	let passbox = <LoginInput show={true} enabled={!isloading} label="Password" valset={setpass} send={()=>{sendlogin(false);}} type="password" />
	let pass2box = <LoginInput show={!signin} enabled={!isloading} label="Confirm Password" valset={setpass2} send={()=>{sendlogin(false);}} type="password" />
	let loginbutton = <div className="flexcenter">
						 <Button disabled={isloading} onClick={()=>sendlogin(false)} variant={isloading?"text":"contained"}>{isloading?(<CircularProgress size="1.5rem" />):(signin?"Login":"Create Account")}</Button>
					  </div>;
	let errordisplay = <div className="flexcenter"><span style={{color:"#f1807e"}}>{expired?"Error: session expired.":errormessage}</span></div>;
	let freebutton = <div className="flexcenter">
				         <Button onClick={()=>{if(isloading) api.abort(); tofreemode();}}>Use Free Version</Button>
					 </div>
	
	return (<div className="flexcenter">
				<LayoutTable style={{marginTop:"50px"}} rows={[[{content:modeswitch}],[{content:namebox}],[{content:passbox}],[{content:pass2box}],
				                                               [{content:loginbutton}],[{content:errormessage!==""||expired?errordisplay:""}],[{content:freebutton}]]} />
			</div>);
}

export default LoginControl;