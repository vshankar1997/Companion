import { FormControl, Grid, InputLabel, MenuItem, Select } from "@mui/material";
import React, { useEffect, useState } from "react";
import logo from "../assets/images/Companion_Logo.svg";
// import logo from "../assets/images/COMPANION.png";
import { useNavigate } from "react-router-dom";
import { useBackgroundColor } from "../BackgroundContext";
import DynamicModal from "./Modal/DynamicModal";
import { api } from "../services/api";
import axios from "axios";

import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
// import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
// import { MenuButton as BaseMenuButton } from '@mui/base/MenuButton';

const Header = () => {
  const navigate = useNavigate();
  const { user_bu, openDocList, setOpenDocList, isGetDocs, buList, buSelected, setBuSelected } = useBackgroundColor();

  const textCapitalize = (text) => {
    return text?.toLowerCase();
  }
  const modalTitle = `${textCapitalize(user_bu)} Collection Documents`;
  const [showList, setShowList] = useState(false)
  const [isBuUpdate, setIsBuUpdate] = useState(false)
  const [docList, setDocList] = useState([])
  const [filteredList, setFilteredList] = useState([]);
  // const [page, setPage] = useState(0);
  // const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  // const [selectedBU, setSelectedBU] = useState(user_bu);

  const navigateUI = () => {
    if (window.location.pathname === "/prompt") {
      navigate("/upload");
    } else {
      navigate("/prompt");
    }
  };

  const handleCloseModal = () => {
    setShowList(false);
    setOpenDocList(false);
    setSearchTerm("");
  };

  const getDocList = () => {
    const getDocData = async () => {
      setDocList([]);
      setFilteredList([]);
      if(buSelected) {   
        try {
          let url = `${process.env.REACT_APP_API_URL}config/doc_list/${buSelected}`
          const response = await api.get(url);
          setDocList(response.data.data);
          setFilteredList(response.data.data);
  
        } catch (error) {
          if (axios.isAxiosError(error)) {
            // Axios-specific error handling
            console.error("Axios Error:", error.message);
            console.error("Response Data:", error.response?.data);
          } else {
            // General error handling
            console.error("Error:", error.message);
          }
        }
      }
    }
    getDocData();
    setShowList(!showList)
    setOpenDocList(true);
  }

  // const handleChangePage = (event, newPage) => {
  //   setPage(newPage);
  // };

  // const handleChangeRowsPerPage = (event) => {
  //   setRowsPerPage(+event.target.value);
  //   setPage(0);
  // };

  const handleSearch = (e) => {
    const term = e.target.value.toLowerCase();
    setSearchTerm(term);

    // Filter the documents based on the search term
    const filtered = docList.filter(doc => {
      // Get the first (and only) key in the document object
      const fileName = Object.keys(doc)[0];
      return fileName.toLowerCase().includes(term);
    });

    window.setTimeout(() => {
      setFilteredList(filtered);
    }, 100)
  };

  const handleBUChange = (e) => {
    setBuSelected(e.target.value);
    setIsBuUpdate(!isBuUpdate)
  }
  
  useEffect(() => {
    setBuSelected(buSelected);
    getDocList();
  }, [isBuUpdate]);
  
  useEffect(() => {
    getDocList();
  }, [isGetDocs])

  const modalContent = (
    <>
      <Paper sx={{ overflow: 'hidden', boxShadow: "none" }}>
        <TableContainer sx={{ maxHeight: 500, overflowX: "hidden" }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead style={{padding: "0px", width: "80%"}}>
              <TableRow>
                <TableCell style={{padding: "5px 0px", border: "none"}}>
                  <TextField
                  style={{
                    width: "40%",
                    maxWidth: "300px",
                    padding: "5px"
                  }}
                    type="text"
                    value={searchTerm}
                    onChange={handleSearch}
                    className="search-input"
                    placeholder="Document Title"
                    label=""
                  />
                  <FormControl style={{
                    marginLeft: "15px",
                    width: "30%",
                    maxWidth: "200px",
                    border: "1px solid #ccc",
                    borderRadius: "7px"
                  }}>
                    <InputLabel id="project-select-label-1"></InputLabel>
                    <Select
                      labelId="project-select-label-1"
                      id="project-select-1"
                      className="bu-select-dropdown"
                      value={buSelected}
                      onChange={(e) => handleBUChange(e)}
                      label="Project"
                      sx={{
                        // borderRadius: "25px",
                        // backgroundColor: "#fff",
                        padding: "0px",
                        '& .MuiSelect-select': {
                          // backgroundColor: "#fff",
                        },
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: '#efefef',
                        },
                        '&:hover': {
                          backgroundColor: "transparent",
                        },
                        '& .MuiSelect-icon': {
                          color: '#000',
                        }
                      }}
                    >
                      {buList?.map((project, index) => (
                        <MenuItem key={index} value={project}>
                          {project}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              <>
              <TableRow
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  hover
                >
                  <TableCell component="th" scope="row" style={{padding: "10px 0px"}}>
                    <span className="bold">
                      Document Title
                    </span>
                  </TableCell>
                </TableRow>
              {/* {filteredList
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((item, index) => */}
              {filteredList.map((item, index) =>
                  (<TableRow
                  key={index}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  hover
                  >
                  <TableCell component="th" scope="row" style={{
                    paddingLeft: "0px"
                  }}>
                    <span className="file-list-">
                      <a href={item[Object.keys(item)[0]]} className="ellipse-text" target="_blank" >{Object.keys(item)[0]} </a>
                    </span>
                  </TableCell>
                </TableRow>)
                )}
              {filteredList.length === 0 && <TableCell component="th" scope="row">
                No record found!
              </TableCell>}
                </>
            </TableBody>
          </Table>
        </TableContainer>
        {/* <TablePagination
          rowsPerPageOptions={[10, 25, 100]}
          component="div"
          count={docList.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        /> */}
      </Paper>
    </>
  );
  const modalActions = (
    <>
    </>
  );

  return (
    <Grid container spacing={12}>
      <Grid
        item
        xs={12}
        display="flex"
        className="text-left"
        justifyContent="left"
      >
        {/* {user_bu !== "" && (window.location.pathname.split("/")[1] === "upload" || window.location.pathname.split("/")[1] === "prompt" || window.location.pathname.split("/")[1] === "c") && <div>
          {!isChat && <p
            className="text-primary d-none"
            style={{
              position: "absolute",
              right: "0px",
              top: "0px",
              width: "225px",
            }}
          >
            CURRENT COLLECTION
            <label className="database-label text-center" onClick={getDocList}>{user_bu}</label>
          </p>}
          {isChat && <p
            className="text-primary d-none"
            style={{
              position: "absolute",
              left: "65px",
              top: "0px",
              width: "225px",
            }}
          >
            CURRENT COLLECTION
            <label className="database-label database-label-chat" onClick={getDocList}>{user_bu}</label>
          </p>}
        </div>} */}
        <div className="text-left header-text">
          <img src={logo} className="main-logo" onClick={navigateUI} alt="main-logo" />
          <span className="ml-3 text-dark header-text-inner" style={{ marginLeft: "15px" }}>
            <i>
              The Private & Secure Gen AI App for Medical Affairs.&nbsp;
              <span className="learn-more" onClick={() => navigate("/faq")}>
                Learn more
              </span>
            </i>
          </span>
        </div>
        {openDocList && docList.length > 0 && <DynamicModal
          isOpen={openDocList}
          onClose={handleCloseModal}
          title={modalTitle}
          content={modalContent}
          actions={modalActions}
        />}
      </Grid>
    </Grid>
  );
};

export default Header;
