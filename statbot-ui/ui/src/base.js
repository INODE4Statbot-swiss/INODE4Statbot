
class APIRequester
{
	aborter = new AbortController();
	logoutf;
	constructor(logoutf) { this.logoutf = logoutf; }
	
	async request(endpoint,body,nextf,errmessage,errf)
	{
		await fetch("/api/"+endpoint,{signal:this.aborter.signal,method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body,null,4)})
				   .then(res=>res.json()).then((data)=>{if(data.status==="ERROR"&&data.error==="INVALID_SESSION_ID") this.logoutf(); else nextf(data); })
				   .catch((e)=>{console.log(errmessage);console.log(e);errf(e);});
	}
	
	abort()
	{
		this.aborter.abort()
		this.aborter = new AbortController();
	}
}

export {APIRequester};
