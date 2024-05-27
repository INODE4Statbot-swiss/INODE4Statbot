import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter,Routes,Route } from 'react-router-dom';
import './index.css';
import App from './App';
import AdminPage from './AdminPage';

const Main = () => {
  return (
    <Routes>
      <Route path='/' element={<App />}></Route>
	  <Route path="/admin" element={<AdminPage />}></Route>
    </Routes>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
	<BrowserRouter>
		<Main />
	</BrowserRouter>
);