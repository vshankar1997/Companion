import {
  BrowserRouter as Router,
  Routes,
  Route,
} from "react-router-dom";
import "./App.css";
import Default from "./Layouts/Default";
import NoHeader from "./Layouts/NoHeader";
import Landing from "./Components/Landing/Landing";
import UserPrompt from "./Components/KnowledgeBase/userPrompt";
import Login from "./Components/Login/Login";
import Faq from "./Components/Faq/Faq";
import { BackgroundProvider } from "./BackgroundContext";
import PromptHistory from "./Components/PromptHistory/PromptHistory";
// import Feedback from "./Components/Feedback/Feedback";
function App() {
  return (
    <BackgroundProvider>
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <NoHeader>
                <Login />
              </NoHeader>
            }
          />
          <Route
            path="/home"
            element={
              <Default>
                <Landing />
              </Default>
            }
          />
          <Route
            path="/prompt"
            element={
              <Default>
                <UserPrompt />
              </Default>
            }
          />
          <Route
            path="/upload"
            element={
              <Default>
                <UserPrompt />
              </Default>
            }
          />
          <Route
            path="/faq"
            element={
              <Default>
                <Faq />
              </Default>
            }
          />
          <Route
            path="/c/:id"
            element={
              <Default>
                <PromptHistory />
              </Default>
            }
          />
          <Route
            path="/*"
            element={
              <Default>
                <UserPrompt />
              </Default>
            }
          />
          {/* <Route
            path="/feedback"
            element={
              <Default>
                <Feedback />
              </Default>
            }
          /> */}
        </Routes>
      </Router>
    </BackgroundProvider>
  );
}

export default App;
