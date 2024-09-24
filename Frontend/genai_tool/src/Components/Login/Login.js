import React, { useEffect, useState } from "react";
import Grid from "@mui/material/Grid";
import {
  Alert,
  Button,
  CircularProgress,
  InputAdornment,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import "../Login/Login.css";
import logo from "../../assets/images/Companion_Logo.svg";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import { api } from "../../services/api";
import axios from "axios";
import OktaAuth from "@okta/okta-auth-js";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [isLogging, setIsLogging] = useState(false);
  const [isValid, setIsValid] = useState(false);
  const isUser = true;
  const isLogin = false;

  const [authClient, setAuthClient] = useState(null);

  useEffect(() => {
    const oktaAuth = new OktaAuth({
      issuer: process.env.REACT_APP_ISSUER,
      clientId: process.env.REACT_APP_CLIENT_ID,
      redirectUri: process.env.REACT_APP_REDIRECTION_URL,
      scopes: process.env.REACT_APP_SCOPES.split(",")
    });
    
    setAuthClient(oktaAuth);
    if (window.location.search.includes('code')) {
      oktaAuth.token.parseFromUrl().then(res => {
        localStorage.setItem("email", res.tokens.idToken.claims?.email);
        validateUser()
      });
    }
  }, []);

  function generateRandomState() {
    const randomBytes = new Uint8Array(16); // 16 bytes = 128 bits
    window.crypto.getRandomValues(randomBytes);
    const stateValue = Array.from(randomBytes)
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
    return stateValue;
  }

  const handleLogin = async () => {
    const randomState = generateRandomState();
    localStorage.setItem("okta-state", randomState);
    try {
      setIsLogging(true);
      await authClient.signInWithRedirect({ state: randomState });
    } catch (error) {
      console.log(error.message);
    }
  };

  /*
  - Function for domain name validation in the email entered user
  - Get the defined domains from env file and check if it macthes with the entered email address.
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  // const validationDomain = () => {
  //   let domains = process.env.REACT_APP_EMAIL_DOMAINS.split(",");
  //   let currDomain = email.split(/[@\s.]+/);
  //   currDomain = currDomain[currDomain.length - 2];
  //   return domains.includes(currDomain);
  // };

  /*
  - Function to validate the user email and then send validate request to api
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const validateUser = async () => {
      try {
        let url = `${process.env.REACT_APP_API_URL}users/validate`;
        const response = await api.post(url, { email: localStorage.getItem("email") });
        const isValidate = response.data.data;
        if (isValidate === "fail") {
          alert("Access deneied, Please contact your administrator!")
        } else {
          navigate("/prompt");
        }
      } catch (error) {
        if (axios.isAxiosError(error)) {
          // Axios-specific error handling
          console.error("Axios Error:", error.message);
          console.error("Response Data:", error.response?.data);
        } else {
          // General error handling
          console.error("Error:", error.message);
        }
        alert("Access deneied, Please contact your administrator!")
      }
  };

  /*
  - Function for validating the email format and handle button state accordingly 
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const handleEmailChange = (e) => {
    const enteredEmail = e.target.value;
    setEmail(enteredEmail);
    if (enteredEmail === "") {
      setIsValid(false);
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const isValidEmail = emailRegex.test(enteredEmail);
      setIsValid(isValidEmail);
    }
  };

  return (
    <Grid container style={{ height: "100vh" }} item xs={12}>
      {/* Left Section */}
      <Grid item sm={6}>
        <Paper
          style={{
            height: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
          className="login-section-left text-center"
        >
          <div>
            <Typography variant="h4">
              <div className="image-colorized-">
                
              <img src={logo} alt="Logo" />
              </div>
            </Typography>
            <p className="pb-3 mt-0">
              <i style={{
              color: "#2E3C49"
            }}>The Private & Secure Gen AI App for Medical Affairs.</i>
            </p>
          </div>
          <Typography variant="h5" maxWidth="sm" className="text-blue">
            <strong style={{
              color: "#2E3C49",
              fontFamily: 'Poppins'
            }}>
              Welcome! I’m <span className="bg-main-text">Companion</span>, your Generative AI partner who can help
              you with your work.
            </strong>
          </Typography>
        </Paper>
      </Grid>

      {/* Right Section */}
      <Grid item sm={6} className="login-section-right">
        <Paper
          style={{
            height: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            flexDirection: "column",
          }}
          className="login-section-right login-section-right-inner"
        >
          <Typography variant="h5" maxWidth="sm" className="text-blue">
            <strong className="text-white" style={{
              fontFamily: 'Poppins'
            }}>Login to your account</strong>
          </Typography>
          <div className="email-section d-none">
            <TextField
              fullWidth
              size="large"
              value={email}
              onKeyDown={(ev) => {
                if (ev.key === "Enter" && !ev.shiftKey) {
                  ev.preventDefault();
                  validateUser();
                }
              }}
              onChange={handleEmailChange}
              sx={{ background: "#fff", border: "none" }}
              placeholder="Email Address"
              className="custom-placeholder"
              style={{
                borderRadius: "100px",
                marginTop: "40px",
                border: "1px solid #E0E0E0",
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailOutlinedIcon />
                  </InputAdornment>
                ),
              }}
            />
            {!isUser && (
              <Alert severity="error" className="mt-1">
                Incorrect email
              </Alert>
            )}
          </div>
          <div className="button-section mt-2 d-none">
            <Button
              variant="contained"
              size="large"
              className="btn-rounded"
              disabled={!isValid}
              onClick={validateUser}
              style={{ width: "100%", padding: "13px" }}
            >
              Login &nbsp;
              {isLogin && (
                <CircularProgress
                  style={{ color: "#fff", height: "20px", width: "20px" }}
                />
              )}
            </Button>
          </div>

          <div>
            <Button className="btn bg-white mt-2 btn-login" variant="contained" onClick={handleLogin} style={{
              color:"#2E3C49",
              textTransform: "capitalize"
            }}>&nbsp;Login with Okta&nbsp;
            {isLogging && <>
              <CircularProgress color="inherit" style={{ color: "#fff", height: "20px", width: "20px" }} />
            </>}
            </Button>
          </div>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default Login;
