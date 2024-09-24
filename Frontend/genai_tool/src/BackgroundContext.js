import React, { createContext, useContext, useEffect, useState } from "react";
import apiService from "./services/appServices";
const BackgroundContext = createContext();
export const useBackgroundColor = () => {
  const context = useContext(BackgroundContext);
  if (!context) {
    throw new Error(
      "useBackgroundColor must be used within a BackgroundProvider"
    );
  }
  return context;
};

export const BackgroundProvider = ({ children }) => {
  const [backgroundColor, setBackgroundColor] = useState("main-bg-linear");
  const [user_bu, setUser_bu] = useState("");
  const [defaultUser_bu, setDefaultUser_bu] = useState("");
  const [buList, setBuList] = useState([]);
  const [buSelected, setBuSelected] = useState("");

  const [isChat, setIsChat] = useState(false);
  const [openDocList, setOpenDocList] = useState(false);
  const [isGetDocs, setIsGetDocs] = useState(false);

  const setNewBackgroundColor = (color) => {
    setBackgroundColor(color);
  };

  const [historyList, setHistoryList] = useState({});
  const [h_session_id, setH_session_id] = useState("");
  const [isUpdate, setIsUpdate] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (localStorage.getItem("email") != null) {
          const result = await apiService("config", "POST", {
            email: localStorage.getItem("email"),
          });
          setHistoryList(result.data?.history_list);
          if(user_bu === "") {
            setUser_bu(result.data?.user_bu);
          }
          setDefaultUser_bu(result.data?.user_bu);
          setBuSelected(result.data?.user_bu);
          setBuList(result.data?.bu_list);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    fetchData();
  }, [isUpdate, user_bu]);

  return (
    <BackgroundContext.Provider
      value={{
        backgroundColor,
        setNewBackgroundColor,
        historyList,
        setHistoryList,
        h_session_id,
        setH_session_id,
        setIsUpdate,
        user_bu,
        setUser_bu,
        isChat,
        setIsChat,
        openDocList,
        setOpenDocList,
        isGetDocs,
        setIsGetDocs,
        defaultUser_bu,
        setDefaultUser_bu,
        buList,
        setBuList,
        buSelected,
        setBuSelected
      }}
    >
      {children}
    </BackgroundContext.Provider>
  );
};
