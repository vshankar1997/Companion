import React, { useEffect } from "react";
import Header from "../Components/Header";
import Footer from "../Components/Footer";
import SideBar from "../Components/SideBar/SideBar";
import { useNavigate } from "react-router-dom";
import { useBackgroundColor } from "../BackgroundContext";
const Default = ({ children }) => {
  const navigate = useNavigate();
  const userMail = localStorage.getItem("email");
  const { backgroundColor, setNewBackgroundColor } = useBackgroundColor();
  useEffect(() => {
    if (userMail == null) {
      navigate("/");
    }
    if (window.location.pathname === "/home") {
      setNewBackgroundColor("main-bg-single");
    }
  }, []);

  return (
    <>
      {userMail && (
        <div className={backgroundColor}>
          <div className="sidebar">
            <SideBar />
          </div>
          <div className="main-content">
            <Header>{/* Header content goes here */}</Header>
            <main>{children}</main>
            <Footer>{/* Footer content goes here */}</Footer>
          </div>
        </div>
      )}
    </>
  );
};

export default Default;
