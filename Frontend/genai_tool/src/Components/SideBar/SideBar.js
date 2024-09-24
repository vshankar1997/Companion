import React, { useEffect, useState } from "react";
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  IconButton,
  ListItemButton,
  styled,
} from "@mui/material";
import { Menu as MenuIcon } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import CloseIcon from "@mui/icons-material/Close";
import ProfilePhoto from "../../assets/images/Profile Photo.png";
import "../SideBar/SideBar.css";
import { useBackgroundColor } from "../../BackgroundContext";
import Tooltip, { TooltipProps, tooltipClasses } from "@mui/material/Tooltip";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import OktaAuth from "@okta/okta-auth-js";

const SideBar = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  // const [authClient, setAuthClient] = useState(null);
  const handleSidebarToggle = () => {
    setSidebarOpen(!isSidebarOpen);
  };
  const { historyList, setHistoryList, setH_session_id, setIsUpdate, isGetDocs, setIsGetDocs  } =
    useBackgroundColor();
  if (Object.keys(historyList).length === 0) {
    setIsUpdate();
  }

  const BootstrapTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} arrow classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.arrow}`]: {
      color: theme.palette.common.black,
    },
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: theme.palette.common.black,
    },
  }));

  useEffect(() => {
    setHistoryList(historyList);
  }, [historyList]);

  useEffect(() => {
    new OktaAuth({
      issuer: process.env.REACT_APP_ISSUER,
      clientId: process.env.REACT_APP_CLIENT_ID,
      redirectUri: process.env.REACT_APP_REDIRECTION_URL,
      scopes: process.env.REACT_APP_SCOPES.split(",")
    });
    // setAuthClient(oktaAuth);
  }, []);

  let win_session =
    window.location.pathname.split("/")[
      window.location.pathname.split("/").length - 1
    ];
  /*
  - Function to handle the logout action
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const handleLogout = () => {
    try {
      // await authClient.signOut();
      localStorage.removeItem("email");
      navigate("/");
    } catch (error) {
      console.log(error.message);
    }
  };

  const navigate = useNavigate();
  const navigateToLanding = (url, isClose) => {
    if (isClose) setSidebarOpen(!isSidebarOpen);
    navigate(url);
  };

  const updateSessionId = (session_id, isClose) => {
    setH_session_id(session_id);
    if (isClose) setSidebarOpen(!isSidebarOpen);
    navigate(`/c/${session_id}`);
  };

  return (
    <div>
      <div>
        <IconButton
          aria-label="open drawer"
          onClick={handleSidebarToggle}
          edge="center"
          className="sidebar-top"
        >
          <MenuIcon className="text-white" style={{ fontSize: "30px" }} />
        </IconButton>
        <Drawer
          anchor="left"
          open={isSidebarOpen}
          variant="persistent"
          onClose={handleSidebarToggle}
          className="sidebar-expanded"
        >
          <div
            style={{
              width: "258px",
              display: "flex",
              flexDirection: "column",
              height: "100vh",
              zIndex: 99999
            }}
          >
            <div style={{ flex: "0 0 5%" }}>
              <IconButton
                onClick={handleSidebarToggle}
                sx={{ float: "right", margin: 1 }}
              >
                <CloseIcon className="text-white" />
              </IconButton>
            </div>

            {/* HISTORY SECTION IN SIDEBAR */}
            <div className="sidebar-item-body">
              <div className="item-body-inner">
                {historyList.today?.map((item, index) => (
                  <>
                    {index === 0 && (
                      <ListItem key={index}>
                        <p className="m-0 text-white font-14 bold">Today</p>
                      </ListItem>
                    )}
                    <ListItem
                      key={index}
                      disablePadding
                      className={
                        win_session === item.session_id ? "active" : ""
                      }
                    >
                      <ListItemButton className="pb-2 pt-2">
                        <BootstrapTooltip
                          title={
                            <React.Fragment>
                              <span color="inherit">{item.chat_title}</span>
                            </React.Fragment>
                          }
                          placement="right"
                        >
                          <ListItemText
                            onClick={() =>
                              updateSessionId(`${item.session_id}`, true)
                            }
                            className="text-primary sidebar-text"
                          >
                            <span className="text-white sidebar-item">{item.chat_title}
                            {item.isUpload && (
                              <AttachFileIcon
                                style={{
                                  position: "absolute",
                                  right: "0px",
                                  fontSize: "18px",
                                  paddingTop: "2px",
                                  paddingRight: "10px",
                                }}
                              />
                            )}</span>
                          </ListItemText>
                        </BootstrapTooltip>
                      </ListItemButton>
                    </ListItem>
                  </>
                ))}
                {historyList.yesterday?.map((item, index) => (
                  <>
                    {index === 0 && (
                      <ListItem>
                        <p className="m-0 text-white font-14 f-500">Yesterday</p>
                      </ListItem>
                    )}
                    <ListItem
                      key={index}
                      disablePadding
                      className={
                        win_session === item.session_id ? "active" : ""
                      }
                    >
                      <ListItemButton className="pb-2 pt-2">
                        <BootstrapTooltip
                          title={
                            <React.Fragment>
                              <span color="inherit">{item.chat_title}</span>
                            </React.Fragment>
                          }
                          placement="right"
                        >
                          <ListItemText
                            onClick={() =>
                              updateSessionId(`${item.session_id}`, true)
                            }
                            className="text-primary sidebar-text"
                          >
                            <span className="text-white sidebar-item">{item.chat_title}
                            {item.isUpload && (
                              <AttachFileIcon
                                style={{
                                  position: "absolute",
                                  right: "0px",
                                  fontSize: "18px",
                                  paddingTop: "2px",
                                  paddingRight: "10px",
                                }}
                              />
                            )}</span>
                          </ListItemText>
                        </BootstrapTooltip>
                      </ListItemButton>
                    </ListItem>
                  </>
                ))}
                {historyList.seven_days?.map((item, index) => (
                  <>
                    {index === 0 && (
                      <ListItem>
                        <p className="m-0 text-white f-500">Previous 7 Days</p>
                      </ListItem>
                    )}
                    <ListItem
                      key={index}
                      disablePadding
                      className={
                        win_session === item.session_id ? "active" : ""
                      }
                    >
                      <ListItemButton className="pb-2 pt-2">
                        <BootstrapTooltip
                          title={
                            <React.Fragment>
                              <span color="inherit">{item.chat_title}</span>
                            </React.Fragment>
                          }
                          placement="right"
                        >
                          <ListItemText
                            onClick={() =>
                              updateSessionId(`${item.session_id}`, true)
                            }
                            className="text-primary sidebar-text"
                          >
                            <span className="text-white sidebar-item">{item.chat_title}
                            {item.isUpload && (
                              <AttachFileIcon
                                style={{
                                  position: "absolute",
                                  right: "0px",
                                  fontSize: "18px",
                                  paddingTop: "2px",
                                  paddingRight: "10px",
                                }}
                              />
                            )}</span>
                          </ListItemText>
                        </BootstrapTooltip>
                      </ListItemButton>
                    </ListItem>
                  </>
                ))}
                {historyList.thirty_days?.map((item, index) => (
                  <>
                    {index === 0 && (
                      <ListItem>
                        <p
                          className="m-0 text-white f-500"
                          style={{ marginTop: "10px" }}
                        >
                          Previous 30 Days
                        </p>
                      </ListItem>
                    )}
                    <ListItem
                      key={index}
                      disablePadding
                      className={
                        win_session === item.session_id && win_session !== ""
                          ? "active"
                          : ""
                      }
                    >
                      <ListItemButton className="pb-2 pt-2">
                        <BootstrapTooltip
                          title={
                            <React.Fragment>
                              <span color="inherit">{item.chat_title}</span>
                            </React.Fragment>
                          }
                          placement="right"
                        >
                          <ListItemText
                            onClick={() =>
                              updateSessionId(`${item.session_id}`, true)
                            }
                            className="text-primary sidebar-text"
                          >
                            <span className="text-white sidebar-item">{item.chat_title}
                            {item.isUpload && (
                              <AttachFileIcon
                                style={{
                                  position: "absolute",
                                  right: "0px",
                                  fontSize: "18px",
                                  paddingTop: "2px",
                                  paddingRight: "10px",
                                }}
                              />
                            )}</span>
                          </ListItemText>
                        </BootstrapTooltip>
                      </ListItemButton>
                    </ListItem>
                  </>
                ))}
              </div>
            </div>
            {/* <Divider className="divider-border" /> */}
            <div className="sidebar-item text-white">
              {[
                { link: "About", target: "/home" },
                { link: "FAQs", target: "/faq" },
              ].map((item, index) => (
                <ListItem
                  key={index}
                  disablePadding
                  className={index === 0 ? "list-border" : ""}
                >
                  <ListItemButton className="pb-2 pt-2">
                    <ListItemText
                      primary={item.link}
                      onClick={() => navigateToLanding(item.target, true)}
                      className="m-0 text-white font-14 bold"
                    />
                  </ListItemButton>
                </ListItem>
              ))}
                <ListItem
                  disablePadding
                >
                  <ListItemButton className="pb-2 pt-2">
                    <ListItemText
                      primary="Collection Details"
                      onClick={() => setIsGetDocs(!isGetDocs)}
                      className="m-0 text-white font-14 bold"
                    />
                  </ListItemButton>
                </ListItem>
              <ListItem
                className="btn-logout font-14 bold text-white font-14 sidebar-text pb-2 pt-2"
                onClick={handleLogout}
              >
                <img src={ProfilePhoto} alt="profile" /> &nbsp; 
                <span style={{
                  float: "right",
                  position: "absolute",
                  right: "10px"
                }}>Logout</span>
              </ListItem>
            </div>
            {/* <List
              className="sidebar-bottom"
              style={{
                // marginTop: "100%",
                // position: "absolute",
                // bottom: "0px",
                width: "100%",
                flex: "0 0 5%",
              }}
            >
            </List> */}
          </div>
        </Drawer>
      </div>
      <div className="sidebar-footer">
        <img src={ProfilePhoto} width={"30px"} alt="profile" onClick={handleSidebarToggle} />
      </div>
    </div>
  );
};

export default SideBar;
