import "../KnowledgeBase/KnowledgeBase.css";
import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import axios from "axios";
import { useDropzone } from "react-dropzone";
// import FileUploadIcon from "@mui/icons-material/FileUpload";
// import LinearProgress from "@mui/material/LinearProgress";
import { useSnackbar } from "notistack";
import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
// import LogoutIcon from "@mui/icons-material/Logout";
import LinearWithValueLabel from "./LinearProgressWithLabel";
import apiService from "../../services/appServices";
import { useBackgroundColor } from "../../BackgroundContext";
const UploadDoc = (props) => {
  let uploadDocHeight =
    props.activeState === 0
      ? window.innerHeight * 0.55
      : window.innerHeight * 0.5;
  const acceptedFileTypes = [
    "application/pdf",
    // "application/msword",
    // "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  const [showFileLoader, setShowFileLoader] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [secToUpload, setSecToUpload] = useState([]);
  const [filesUploaded, setFilesUploaded] = useState(false);
  const [uploadRate, setUploadRate] = useState(0);
  const { enqueueSnackbar } = useSnackbar();
  
  const { setIsChat, user_bu } = useBackgroundColor()
  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiService("config", "POST", {
          email: localStorage.getItem("email"),
        });
        setUploadRate(result.data?.upload_rate);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    fetchData();
  }, []);

  let maxFileSizeLimit = 50000000;
  // let maxFileSizeLimit = 25000000;
  const notifyUser = (msg, variant) => {
    enqueueSnackbar(msg, {
      variant,
      anchorOrigin: {
        vertical: "top",
        horizontal: "right",
      },
    });
  };

  const onDrop = (acceptedFiles, rejectedFiles) => {
    // Check if all dropped files have valid types
    let uploadingFiles = [];
    let fileCount = 0;
    let fileSize = 0;
    setFilesUploaded(false);

    let fileProgressArr = [];
    acceptedFiles.forEach((file) => {
      acceptedFileTypes.includes(file.type);
      if (acceptedFileTypes.includes(file.type)) {
        fileCount++;
        fileSize += file.size;
        let fileProgress = (file.size / uploadRate + 10) * 60;
        fileProgressArr.push(fileProgress);
        setSecToUpload(fileProgressArr);
        uploadingFiles.push(file);
      }
    });
    
    if (fileCount <= 5 && fileSize < maxFileSizeLimit) {
      // setSecToUpload((fileSize / uploadRate + 10) * 60);
      setShowFileLoader(true);
      localStorage.setItem("isUpload", "true");
      window.setTimeout(() => {
      if (localStorage.getItem("isUpload") === "true") {
        notifyUser("This process may take sometime to complete.", "info");
      }
    }, 30000);
      let cState = props.currentState;
      cState = {
        ...cState,
        isLoading: true,
      };
      props.setCurrentState(cState);
      uploadingFiles.sort((a, b) => a.path.localeCompare(b.path));
      props.setSelectedFiles([...uploadingFiles]);
      if (fileCount === acceptedFiles.length) {
        uploadFiles(
          fileCount,
          acceptedFiles,
          uploadingFiles,
          "Files uploaded successfully!",
          "success"
        );
      } else if (fileCount > 0) {
        uploadFiles(
          fileCount,
          acceptedFiles,
          uploadingFiles,
          "Pdfs files are uploaded successfully!\n Skipped other formatted files.",
          "warning"
        );
      } else {
        notifyUser("Please upload the correct files.", "warning");
      }
    } else if (fileCount > 5) {
      notifyUser("Max 5 files can be uploaded!", "warning");
    } else {
      notifyUser("Max only 50MB of files can be uploaded!", "warning");
    }
    // Handle rejected files (e.g., show an error message)
    if (rejectedFiles && rejectedFiles.length > 0) {
      console.error("Rejected Files:", rejectedFiles);
    }
  };

  const uploadFiles = async (fileCount, acceptedFiles, files, msg, variant) => {
    const formData = new FormData();
    // Append each selected file to the form data
    files.forEach((file, index) => {
      formData.append(file.name, file);
    });
    formData.append("email", localStorage.getItem("email"));
    formData.append("user_bu", user_bu);

    let url = `${process.env.REACT_APP_API_URL}upload_prompt/upload`;
    await axios
      .post(url, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        // onUploadProgress: (progressEvent) => {
        //   const percentage = Math.round(
        //     (progressEvent.loaded * 100) / progressEvent.total
        //   );
        //   console.log("progressEvent", progressEvent);
        // },
      })
      .then((response) => {
        setIsChat(true);
        setFilesUploaded(true);
        setFilesUploaded(false);
        notifyUser(msg, variant);
        let cState = props.currentState;
        cState = {
          ...cState,
          isLoading: false,
        };
        setShowFileLoader(false);
        localStorage.setItem("isUpload", "false");
        props.setCurrentState(cState);
        props.setActiveState(1);
        props.setStepCompleted(1);
        setFileUploaded(true);
        props.setUploadSessionId(response.data.data?.session_id);
      })
      .catch((error) => {
        notifyUser("Something went wrong. Please try again.", "warning");
        console.error("Upload failed:", error);
        setShowFileLoader(false);
        localStorage.setItem("isUpload", "false");
        let cState = props.currentState;
        cState = {
          ...cState,
          isLoading: false,
        };
        props.setCurrentState(cState);
        props.setSelectedFiles([]);
      });
  };

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    multiple: true, // Set to true for multiple file upload
  });

  return (
    <>
      {props.activeState === 0 && <div
        className={`${props.activeState === 0
            ? "upload-doc-wrapper-before"
            : "upload-doc-wrapper-after"
          }`}
      >
        <div
          className="upload-doc-container"
          style={{ height: uploadDocHeight+10, width: uploadDocHeight+10 }}
        >
          <div
            className={
              props.activeState !== 1 ? "upload-doc cursor-pointer" : "upload-doc"
            }
            style={{
              height: uploadDocHeight - 40,
              width: uploadDocHeight - 40,
            }}
          >
            {props.selectedFiles?.length === 0 && (
              <div
                {...getRootProps({
                  className: `dropzone ${isDragActive ? "active" : ""} ${isDragAccept ? "accept" : ""
                    } ${isDragReject ? "reject" : ""}`,
                })}
                style={{ flex: 1, textAlign: "center" }}
              >
                <input {...getInputProps()} accept="application/pdf" />
                <h3 className="text-dark upload-doc-prompt">
                  Add documents to get started
                </h3>
                <p
                  className="text-small mt-0"
                  style={{ width: "90%", marginLeft: "5%" }}
                >
                  Summarize a set of notes, draft insights, create a presentation
                  outline, and more{" "}
                </p>
                <span className="text-primary fw-500" style={{
                  textDecoration:"underline"
                }}>
                  Click to upload
                </span> or drag and drop
                {/* <div className="text-primary">
                  <FileUploadIcon />
                  <p className="m-0 upload-icon">
                    <LogoutIcon className="font-20" />
                  </p>
                </div> */}
                <div className="upload-info-wrapper text-center">
                  <p className="small text-muted upload-info">
                    PDF (max. 5 files and/or 50MB)
                  </p>
                </div>
              </div>
            )}
            {props.selectedFiles?.length > 0 && (
              <div style={{ width: "100%" }}>
                <ul>
                  {props.selectedFiles.map((file, index) => (
                    <>
                      <li
                        key={index}
                        className="pdf-list text-left text-primary mt-1"
                      >
                        {file.name}
                        {showFileLoader && (
                          <Box sx={{ width: "100%", paddingTop: "5px" }}>
                            {/* <LinearProgress
                            style={{
                              background: "#FFF",
                              height: "10px",
                            }}
                          /> */}
                            <LinearWithValueLabel
                              secToUpload={secToUpload[index]}
                              filesUploaded={filesUploaded}
                            />
                          </Box>
                        )}
                      </li>
                      {fileUploaded && (
                        <>
                          <div style={{ position: "relative" }}>
                            <CheckCircleOutlineOutlinedIcon
                              className="text-primary files-upload-success"
                              style={{ fontSize: "16px" }}
                            />
                          </div>
                        </>
                      )}
                    </>
                  ))}
                  {fileUploaded && (
                    <div className="upload-info-wrapper">
                      <p
                        size="small"
                        className="small text-muted upload-info-files"
                      >
                        Uploads can be PDF documents. Upload up to 5 files or
                        50MB.
                      </p>
                    </div>
                  )}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>}
    </>
  );
};

export default UploadDoc;
