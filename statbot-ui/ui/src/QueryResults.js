import React,{useEffect,useState,Component,Fragment} from 'react';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import ChevronRight from '@mui/icons-material/ChevronRight';
import ChevronLeft from '@mui/icons-material/ChevronLeft';
import Paper from '@mui/material/Paper';
import TableContainer from '@mui/material/TableContainer';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableHead from '@mui/material/TableHead';
import TableFooter from '@mui/material/TableFooter';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import {styled} from '@mui/material/styles';

import {LoadingDisplay} from './Utils.js';

const StyledTableRow = styled(TableRow)(({theme}) => ({'&:nth-of-type(odd)':{backgroundColor:theme.palette.action.hover}}));

function NLExplanation(props)
{
	const {show,explanation,...other} = props;
	return (show?<Box display="flex" justifyContent="center" alignItems="center">
							 <div style={{whiteSpace:"pre-wrap",maxWidth:"800px",borderRadius:"10px",border:"3px solid silver",background:"whitesmoke",padding:"20px",marginLeft:"50px",marginRight:"50px",boxShadow:"5px 5px 2px 1px rgba(0, 0, 0, 0.2)",fontFamily:"Calibri"}}>{explanation}</div>
				 </Box>:"");
}

function ResultsTable(props)
{
	const {st,message,colnames,rows,...other} = props;
	const [page,setpage] = React.useState(0);
	return (st==="OK"?
				<Box display="flex" justifyContent="center" alignItems="center"><div style={{overflowX:"auto",paddingTop:"10px",paddingBottom:"10px",paddingLeft:"20px",paddingRight:"30px",maxWidth:"80vw"}}><TableContainer component={Paper} style={{width:"max-content"}}><Table>
					<TableHead><TableRow style={{backgroundColor:"#888888"}}>
						{colnames.map((nm,i)=>(<TableCell style={{color:"white",border:"none",paddingLeft:"50px",paddingRight:"50px"}} key={""+i}>
													<Box display="flex" justifyContent="center" alignItems="center">{nm}</Box>
											   </TableCell>))}
					</TableRow></TableHead>
				<TableBody>
					{rows.slice(page*10,(page+1)*10).map((rw,i)=>(<StyledTableRow key={""+i}>{rw.map((v,j)=>(<TableCell style={{paddingLeft:"50px",paddingRight:"50px"}} key={""+i+"|"+j}>
																						<Box display="flex" justifyContent="center" alignItems="center">{v}</Box>
																				  </TableCell>))}</StyledTableRow>))}
			    </TableBody><TableFooter><TableRow><TableCell colSpan={colnames.length}><Box display="flex" justifyContent="right" alignItems="center">
				{"Rows "+((page*10)+1)+" to "+(((page+1)*10)<=rows.length?((page+1)*10):rows.length)+" of "+rows.length}
				<Button disabled={page===0} onClick={()=>{if(page>0)setpage(page-1);}}><ChevronLeft /></Button>
				<Button disabled={page>=((rows.length/10)-1)} onClick={()=>{if(page<((rows.length/10)-1))setpage(page+1);}}><ChevronRight /></Button>
				</Box></TableCell></TableRow></TableFooter></Table></TableContainer></div></Box>
				:<Box display="flex" justifyContent="center" alignItems="center">{(st==="EMPTY"?"No results found.":<span style={{fontFamily:"Courier",whiteSpace:"pre-wrap",maxWidth:"132ch",wordWrap:"break-word"}}>{"Error: "+message}</span>)}</Box>);
}

export {NLExplanation,ResultsTable};