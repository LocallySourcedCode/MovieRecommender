import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './styles.css'
import { App } from './App'
import { SignIn } from './pages/SignIn'
import { CreateGroup } from './pages/CreateGroup'
import { JoinGroup } from './pages/JoinGroup'
import { GroupLobby } from './pages/GroupLobby'
import { NominateGenres } from './pages/NominateGenres'
import { VoteGenres } from './pages/VoteGenres'
import { Movies } from './pages/Movies'

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
          <Route path="g/:code/nominate-genres" element={<NominateGenres />} />
          <Route path="g/:code/vote-genres" element={<VoteGenres />} />
          <Route path="g/:code/movies" element={<Movies />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
