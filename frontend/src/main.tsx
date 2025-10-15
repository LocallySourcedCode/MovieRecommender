import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { App } from './App'
import { SignIn } from './pages/SignIn'
import { CreateGroup } from './pages/CreateGroup'
import { JoinGroup } from './pages/JoinGroup'
import { GroupLobby } from './pages/GroupLobby'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}> 
          <Route index element={<Navigate to="/groups/new" replace />} />
          <Route path="signin" element={<SignIn />} />
          <Route path="groups/new" element={<CreateGroup />} />
          <Route path="join" element={<JoinGroup />} />
          <Route path="g/:code" element={<GroupLobby />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
