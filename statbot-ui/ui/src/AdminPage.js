import './AdminPage.css';
import {useState} from 'react';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';

import {APIRequester} from './base.js';
import {LayoutTable} from './Utils.js';

function AdminPage()
{
	const [pass,setpass] = useState("");
	const [username,setusername] = useState("");
	const [isloading,setisloading] = useState(false);
	const [api,setapi] = useState(()=>new APIRequester(()=>{;}));
	const [errmessage,seterrmessage] = useState("");
	const [errstate,seterrstate] = useState(0);
	
	function procresponse(data,successmsg)
	{
		if(data.status==="ERROR")
     	{
			seterrstate(1);
			if(data.error==="INVALID_PASSWORD")
				seterrmessage("Incorrect admin password.");
			else if(data.error==="FORBIDDEN")
				seterrmessage("Operation not permitted.");
			else
				seterrmessage("Unknown error.")
		}
		else
		{
			seterrstate(0);
			seterrmessage(successmsg);
		}
		setisloading(false);
	}
	
	async function addtowhitelist(pw,user)
	{
		setisloading(true);
		seterrmessage("");
		seterrstate(0);
		await api.request("admin",{"command":"add","password":pw,"username":user},
						  (data)=>{procresponse(data,"User added to whitelist.")},
						  "Error adding to whitelist.",
						  (e)=>{seterrstate(1);seterrmessage("Error connecting to server.");setisloading(false);});
	}
	
	async function removefromwhitelist(pw,user)
	{
		setisloading(true);
		seterrmessage("");
		seterrstate(0);
		await api.request("admin",{"command":"remove","password":pw,"username":user},
						  (data)=>{procresponse(data,"User removed from whitelist.")},
						  "Error removing from whitelist.",
						  (e)=>{seterrstate(1);seterrmessage("Error connecting to server.");setisloading(false);});
	}
	
	async function resetpassword(pw,user)
	{
		setisloading(true);
		seterrmessage("");
		seterrstate(0);
		await api.request("admin",{"command":"reset","password":pw,"username":user},
						  (data)=>{procresponse(data,"User password reset.")},
						  "Error removing user password.",
						  (e)=>{seterrstate(1);seterrmessage("Error connecting to server.");setisloading(false);});
	}
	
	let title = <h1>Statbot Admin Control Panel</h1>;
	let passbox = <TextField disabled={isloading} onChange={(e)=>setpass(e.target.value)} label="Admin Password" type="password"></TextField>;
	
	let usernamebox = <TextField disabled={isloading} onChange={(e)=>setusername(e.target.value)} label="Username"></TextField>;
	let addbutton = <Button disabled={isloading || username===""} onClick={()=>addtowhitelist(pass,username)}>Add to Whitelist</Button>;
	let removebutton = <Button disabled={isloading || username===""} onClick={()=>removefromwhitelist(pass,username)}>Remove from Whitelist</Button>;
	let resetbutton = <Button disabled={isloading || username===""} onClick={()=>resetpassword(pass,username)}>Reset User Password</Button>;
	
	let responsemsg = <div className="flexcenter" style={{color:errstate?"red":"green"}}>{errmessage}</div>
	
	return (<div className="flexcenter" style={{paddingTop:"5%",paddingLeft:"5%",paddingRight:"5%"}}>
				<LayoutTable style={{marginTop:"30px"}} rows={[[{content:title}],
															   [{content:passbox}],
															   [{content:usernamebox}],
															   [{content:responsemsg}],
															   [{content:addbutton}],
															   [{content:removebutton}],
															   [{content:resetbutton}]]} />
	        </div>);
	
}

export default AdminPage;