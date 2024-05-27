import './Utils.css';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';

function TableBP(props)
{
	const {children,...other} = props;
	return (<table className="layout" {...other}><tbody>{children}</tbody></table>);
}

function LayoutTable(props)
{
	const {rows,...other} = props;
	return (<TableBP {...other}>
				{rows.map((cols,i)=>(<tr className="layout" key={""+i}>{cols.map((col,j)=>(<td className="layout" key={""+i+""+j} style={col.width?{width:col.width}:{}}>{col.content}</td>))}</tr>))}
			</TableBP>);
}

function FatalError(props)
{
	const {...other} = props;
	return (<div className="flexcenter"><pre>Error connecting to server.</pre></div>);
}

function LoadingDisplay(props)
{
	const {show,message,abort,...other} = props;
	return (show?(<div className="flexcenter">
				      <CircularProgress />&nbsp;{message}...&nbsp;<Button onClick={()=>{abort();}}>Cancel</Button>
				  </div>):"");
}

export {TableBP, LayoutTable, FatalError, LoadingDisplay};