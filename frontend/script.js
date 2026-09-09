"use strict";



//CONFIGURATION


const API_BASE_URL = "http://localhost:8000";
const WEBSOCKET_URL = "ws://localhost:8000/ws/chat";


//STATE


let socket = null;

let currentAssistantMessage = null;
let currentAssistantRawText = "";

let currentDocumentId = null;
let currentDocumentName = "";

let isUploading = false;
let isSending = false;

let reconnectTimer = null;


//DOM HELPER


function getElement(id) {
    return document.getElementById(id);
}


//CONNECTION STATUS


function setConnectionStatus(online, text) {
    const status = getElement("connectionStatus");

    if (!status) {
        return;
    }

    status.classList.remove("online", "offline");
    status.classList.add(online ? "online" : "offline");

    status.innerHTML = `
        <span class="status-dot"></span>
        ${escapeHtml(text)}
    `;
}


//HTML ESCAPE


function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


//CLEAN ASSISTANT RESPONSE

function cleanAssistantText(text) {
    if (!text) {
        return "";
    }

    let cleaned = String(text);

    /* Normalize line endings */
    cleaned = cleaned.replace(/\r\n/g, "\n");
    cleaned = cleaned.replace(/\r/g, "\n");

    /* Remove markdown headings */
    cleaned = cleaned.replace(/^\s*#{1,6}\s*/gm, "");

    /* Remove bold */
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/gs, "$1");
    cleaned = cleaned.replace(/__(.*?)__/gs, "$1");

    /* Remove italic */
    cleaned = cleaned.replace(
        /(^|[\s(])\*([^\*\n]+)\*(?=[\s).,!?]|$)/g,
        "$1$2"
    );

    cleaned = cleaned.replace(
        /(^|[\s(])_([^_\n]+)_(?=[\s).,!?]|$)/g,
        "$1$2"
    );

    /* Remove bullet markers */
    cleaned = cleaned.replace(/^\s*[-•*]\s+/gm, "");

    /* Remove numbered list markers */
    cleaned = cleaned.replace(/^\s*\d+\.\s+/gm, "");

    /* Remove inline code markers */
    cleaned = cleaned.replace(/`/g, "");

    /* Convert markdown links to text */
    cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

    /* Remove horizontal separators */
    cleaned = cleaned.replace(/^\s*([-*_]){3,}\s*$/gm, "");

    /* Remove remaining markdown asterisks */
    cleaned = cleaned.replace(/\*/g, "");

    /* Remove excessive spaces */
    cleaned = cleaned.replace(/[ \t]{2,}/g, " ");

    /* Remove excessive blank lines */
    cleaned = cleaned.replace(/\n{3,}/g, "\n\n");

    return cleaned.trim();
}


//CREATE CHAT MESSAGE

function createMessage(type, text = "") {
    const chatBox = getElement("chatBox");

    if (!chatBox) {
        console.error("chatBox element not found.");
        return null;
    }

    /* Remove welcome message */
    const welcome = chatBox.querySelector(".welcome-message");

    if (welcome) {
        welcome.remove();
    }

    /* Create message row */
    const row = document.createElement("div");
    row.className = `chat-message-row ${type}-row`;

    /* Create content wrapper */
    const content = document.createElement("div");
    content.className = "chat-message-content";

    /* Create message */
    const message = document.createElement("div");
    message.className = `message ${type}`;

    /*
       textContent is intentional.
       It prevents AI-generated content from becoming HTML.
    */
    message.textContent = text;

    content.appendChild(message);
    row.appendChild(content);
    chatBox.appendChild(row);

    scrollChatToBottom();

    return message;
}


//SCROLL CHAT

function scrollChatToBottom() {
    const chatBox = getElement("chatBox");

    if (!chatBox) {
        return;
    }

    requestAnimationFrame(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}


//WEBSOCKET CONNECT

function connectWebSocket() {
    if (
        socket &&
        (
            socket.readyState === WebSocket.OPEN ||
            socket.readyState === WebSocket.CONNECTING
        )
    ) {
        return;
    }

    if (!navigator.onLine) {
        setConnectionStatus(false, "Offline");
        return;
    }

    console.log("Connecting to WebSocket...");

    setConnectionStatus(false, "Connecting...");

    try {
        socket = new WebSocket(WEBSOCKET_URL);
    } catch (error) {
        console.error("WebSocket creation failed:", error);

        socket = null;

        setConnectionStatus(false, "Connection failed");

        scheduleReconnect();

        return;
    }


    //OPEN
   

    socket.onopen = function () {
        console.log("WebSocket connected successfully.");

        setConnectionStatus(true, "Connected");

        updateQuestionState();
    };


    //MESSAGE
    

    socket.onmessage = function (event) {
        handleWebSocketMessage(event);
    };


    // ERROR
    

    socket.onerror = function (error) {
        console.error("WebSocket error:", error);

        setConnectionStatus(false, "Connection error");
    };


    //CLOSE
    

    socket.onclose = function () {
        console.log("WebSocket disconnected.");

        socket = null;

        setConnectionStatus(false, "Disconnected");

        /*
           Do not leave the UI permanently locked
           if the backend disconnects.
        */
        isSending = false;

        currentAssistantMessage = null;
        currentAssistantRawText = "";

        updateQuestionState();

        scheduleReconnect();
    };
}


//RECONNECT


function scheduleReconnect() {
    if (reconnectTimer) {
        return;
    }

    if (!navigator.onLine) {
        return;
    }

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, 2000);
}


//HANDLE WEBSOCKET MESSAGE


function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);

        console.log("WebSocket message:", data);


        //RETRIEVAL
        

        if (data.type === "retrieval") {
            currentAssistantRawText = "";

            currentAssistantMessage = createMessage(
                "assistant",
                ""
            );

            scrollChatToBottom();

            return;
        }


        // TOKEN
       

        if (data.type === "token") {
            if (!currentAssistantMessage) {
                currentAssistantRawText = "";

                currentAssistantMessage = createMessage(
                    "assistant",
                    ""
                );
            }

            const token = data.content || "";

            currentAssistantRawText += token;

            const cleanedText = cleanAssistantText(
                currentAssistantRawText
            );

            if (currentAssistantMessage) {
                currentAssistantMessage.textContent =
                    cleanedText;
            }

            scrollChatToBottom();

            return;
        }


        //DONE
       
        if (data.type === "done") {
            if (currentAssistantMessage) {
                currentAssistantMessage.textContent =
                    cleanAssistantText(
                        currentAssistantRawText
                    );
            }

            currentAssistantMessage = null;
            currentAssistantRawText = "";

            isSending = false;

            updateQuestionState();
            updateClearButton();

            scrollChatToBottom();

            return;
        }


        //ERROR
       

        if (data.type === "error") {
            const errorMessage =
                data.message ||
                data.detail ||
                "Something went wrong.";

            if (currentAssistantMessage) {
                currentAssistantMessage.textContent =
                    "Error: " + errorMessage;
            } else {
                createMessage(
                    "assistant",
                    "Error: " + errorMessage
                );
            }

            currentAssistantMessage = null;
            currentAssistantRawText = "";

            isSending = false;

            updateQuestionState();
            updateClearButton();

            console.error(
                "Backend error:",
                errorMessage
            );

            return;
        }


        //UNKNOWN MESSAGE
       

        console.warn(
            "Unknown WebSocket message type:",
            data.type
        );

    } catch (error) {
        console.error(
            "Invalid WebSocket message:",
            event.data,
            error
        );

        currentAssistantMessage = null;
        currentAssistantRawText = "";

        isSending = false;

        updateQuestionState();

        createMessage(
            "assistant",
            "Received an invalid response from the server."
        );
    }
}


//SEND QUESTION


function sendQuestion() {
    const input = getElement("question");

    if (!input) {
        console.error("Question input not found.");
        return;
    }

    const question = input.value.trim();

    /* Empty question */
    if (!question) {
        updateClearButton();
        return;
    }


    //PDF REQUIRED
    

    if (!currentDocumentId) {
        createMessage(
            "assistant",
            "Please upload a PDF before asking a question."
        );

        return;
    }


    //PREVENT DUPLICATE REQUEST
   

    if (isSending) {
        return;
    }


    //WEBSOCKET REQUIRED
   

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        createMessage(
            "assistant",
            "WebSocket is not connected. Please wait a moment and try again."
        );

        connectWebSocket();

        return;
    }


    //SHOW USER MESSAGE
    

    createMessage(
        "user",
        question
    );


    //RESET ASSISTANT
    

    currentAssistantMessage = null;
    currentAssistantRawText = "";


    //SENDING STATE
   

    isSending = true;

    updateQuestionState();


    //PAYLOAD
   

    const payload = {
        message: question,
        document_id: currentDocumentId
    };

    console.log(
        "Sending question:",
        payload
    );


    //SEND
    

    try {
        socket.send(
            JSON.stringify(payload)
        );
    } catch (error) {
        console.error(
            "Failed to send WebSocket message:",
            error
        );

        isSending = false;

        updateQuestionState();

        createMessage(
            "assistant",
            "Failed to send your question. Please try again."
        );

        return;
    }


    //CLEAR INPUT
  

    input.value = "";

    updateClearButton();
}


//CLEAR INPUT


function clearQuestion() {
    const input = getElement("question");

    if (!input) {
        return;
    }

    if (isSending) {
        return;
    }

    input.value = "";

    updateClearButton();

    input.focus();
}


//UPDATE CLEAR BUTTON


function updateClearButton() {
    const input = getElement("question");
    const clearButton = getElement("clearButton");

    if (!input || !clearButton) {
        return;
    }

    const hasText =
        input.value.trim().length > 0;

    clearButton.disabled =
        !hasText || isSending;

    clearButton.classList.toggle(
        "visible",
        hasText && !isSending
    );
}


//ENTER KEY


function handleEnter(event) {
    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {
        event.preventDefault();

        sendQuestion();
    }
}


//UPDATE QUESTION STATE


function updateQuestionState() {
    const input = getElement("question");
    const button = getElement("sendButton");

    if (!input || !button) {
        return;
    }

    const websocketReady =
        socket &&
        socket.readyState === WebSocket.OPEN;

    const canSend =
        Boolean(
            currentDocumentId &&
            websocketReady &&
            !isSending
        );


    /* Enable / disable input */
    input.disabled = !canSend;

    button.disabled = !canSend;


    //SEND BUTTON
   

    const buttonIcon =
        button.querySelector(".button-icon");

    const buttonText =
        button.querySelector(".button-text");


    if (isSending) {
        if (buttonIcon) {
            buttonIcon.innerHTML = `
                <span class="send-spinner"></span>
            `;
        }

        if (buttonText) {
            buttonText.textContent = "Thinking...";
        }

    } else {
        if (buttonIcon) {
            buttonIcon.innerHTML = `
                <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    aria-hidden="true"
                >
                    <path d="M22 2L11 13"></path>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                </svg>
            `;
        }

        if (buttonText) {
            buttonText.textContent = "Send";
        }
    }


    //PLACEHOLDER
   

    if (isSending) {
        input.placeholder = "AI is thinking...";

    } else if (currentDocumentId) {
        input.placeholder =
            "Ask a question about your PDF...";

    } else {
        input.placeholder =
            "Upload a PDF first...";
    }


    updateClearButton();
}


//SETUP CHAT INPUT


function setupChatInput() {
    const input = getElement("question");
    const sendButton = getElement("sendButton");
    const clearButton = getElement("clearButton");


    //INPUT
    

    if (input) {
        input.addEventListener(
            "input",
            function () {
                updateClearButton();
            }
        );

        input.addEventListener(
            "keydown",
            handleEnter
        );
    }


    //SEND
   

    if (sendButton) {
        sendButton.addEventListener(
            "click",
            function () {
                sendQuestion();
            }
        );
    }


    //CLEAR
   

    if (clearButton) {
        clearButton.addEventListener(
            "click",
            function () {
                clearQuestion();
            }
        );
    }


    updateClearButton();
}


//FILE INPUT


function setupFileInput() {
    const fileInput = getElement("pdfFile");
    const fileName = getElement("fileName");

    if (!fileInput) {
        console.error("pdfFile element not found.");
        return;
    }

    fileInput.addEventListener(
        "change",
        function () {
            if (
                !fileInput.files ||
                fileInput.files.length === 0
            ) {
                if (fileName) {
                    fileName.textContent =
                        "Choose a PDF file";
                }

                return;
            }

            const file = fileInput.files[0];

            if (fileName) {
                fileName.textContent = file.name;
            }
        }
    );
}


//UPLOAD PDF


async function uploadPDF() {
    if (isUploading) {
        return;
    }

    const fileInput = getElement("pdfFile");
    const uploadButton = getElement("uploadButton");

    if (!fileInput) {
        console.error(
            "PDF file input not found."
        );

        return;
    }


    //CHECK FILE
   

    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {
        setUploadStatus(
            "Please select a PDF file.",
            "error"
        );

        return;
    }

    const file = fileInput.files[0];


    //VALIDATE PDF
   

    const isPDF =
        file.type === "application/pdf" ||
        file.name
            .toLowerCase()
            .endsWith(".pdf");

    if (!isPDF) {
        setUploadStatus(
            "Only PDF files are allowed.",
            "error"
        );

        fileInput.value = "";

        return;
    }


    //OPTIONAL SIZE CHECK
    

    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {
        setUploadStatus(
            "PDF is too large. Maximum size is 10 MB.",
            "error"
        );

        fileInput.value = "";

        return;
    }


    //START UPLOAD
    
    isUploading = true;

    if (uploadButton) {
        uploadButton.disabled = true;
        uploadButton.textContent = "Uploading...";
    }

    setUploadStatus(
        "Uploading and indexing PDF...",
        ""
    );


    const formData = new FormData();

    formData.append(
        "file",
        file
    );


    //SEND TO FASTAPI
   

    try {
        console.log(
            "Uploading PDF:",
            file.name
        );

        const response = await fetch(
            `${API_BASE_URL}/upload-pdf`,
            {
                method: "POST",
                body: formData
            }
        );


        //READ RESPONSE
        

        const responseText =
            await response.text();

        let data = {};

        try {
            data = responseText
                ? JSON.parse(responseText)
                : {};

        } catch (jsonError) {
            console.error(
                "Invalid JSON:",
                responseText
            );

            throw new Error(
                "Server returned an invalid response."
            );
        }


        //BACKEND ERROR
       

        if (!response.ok) {
            let message =
                "PDF upload failed.";

            if (
                typeof data.detail === "string"
            ) {
                message = data.detail;

            } else if (
                Array.isArray(data.detail)
            ) {
                message = data.detail
                    .map(
                        item => item.msg || ""
                    )
                    .filter(Boolean)
                    .join(", ");
            }

            throw new Error(message);
        }


        //DOCUMENT ID
       

        if (!data.document_id) {
            throw new Error(
                "Upload succeeded, but the server did not return document_id."
            );
        }


        // SAVE DOCUMENT
     

        currentDocumentId =
            data.document_id;

        currentDocumentName =
            data.document ||
            data.filename ||
            file.name;


        console.log(
            "Document uploaded:",
            currentDocumentId
        );


        // UPLOAD SUCCESS
      

        setUploadStatus(
            `PDF uploaded successfully. Pages: ${
                data.pages || 0
            }, Chunks: ${
                data.chunks || 0
            }`,
            "success"
        );


        // SHOW DOCUMENT CARD

        showDocument({
            document: currentDocumentName,
            pages: data.pages || 0,
            chunks: data.chunks || 0
        });


        // ADD TO KNOWLEDGE BASE
       

        addDocumentToKnowledgeBase({
            document_id: data.document_id,
            document: currentDocumentName,
            pages: data.pages || 0,
            chunks: data.chunks || 0,
            size: formatFileSize(file.size),
            status: "Indexed"
        });


        // CHAT SUCCESS MESSAGE
        

        createMessage(
            "assistant",
            `Document "${currentDocumentName}" is ready. You can now ask questions about it.`
        );


        // CLEAR FILE PICKER
        

        fileInput.value = "";

        const fileNameElement =
            getElement("fileName");

        if (fileNameElement) {
            fileNameElement.textContent =
                "Choose a PDF file";
        }


        // ENABLE CHAT
       

        updateQuestionState();


        // FOCUS CHAT
       

        const question =
            getElement("question");

        if (
            question &&
            !question.disabled
        ) {
            setTimeout(() => {
                question.focus();
            }, 100);
        }

    } catch (error) {
        console.error(
            "PDF upload error:",
            error
        );

        setUploadStatus(
            "Error: " +
            (
                error.message ||
                "PDF upload failed."
            ),
            "error"
        );

    } finally {
        isUploading = false;

        if (uploadButton) {
            uploadButton.disabled = false;
            uploadButton.textContent =
                "Upload PDF";
        }
    }
}


// ADD DOCUMENT TO KNOWLEDGE BASE


function addDocumentToKnowledgeBase(documentData) {
    const documentList =
        getElement("documentList");

    if (!documentList) {
        console.warn(
            "documentList not found."
        );

        return;
    }


    /* Remove empty state */
    const emptyState =
        documentList.querySelector(
            ".document-empty"
        );

    if (emptyState) {
        emptyState.remove();
    }


    // PREVENT DUPLICATES
   

    const existingRow =
        documentList.querySelector(
            `[data-document-id="${CSS.escape(
                String(documentData.document_id)
            )}"]`
        );

    if (existingRow) {
        existingRow.remove();
    }


    // CREATE ROW
    

    const row =
        document.createElement("div");

    row.className =
        "document-row";

    row.dataset.documentId =
        documentData.document_id;


    // FILE COLUMN
    

    const fileColumn =
        document.createElement("div");

    fileColumn.className =
        "document-file";


    const icon =
        document.createElement("div");

    icon.className =
        "document-icon";

    icon.textContent =
        "PDF";


    const name =
        document.createElement("div");

    name.className =
        "document-name";

    name.title =
        documentData.document;

    name.textContent =
        documentData.document;


    fileColumn.appendChild(icon);
    fileColumn.appendChild(name);


    // STATUS
    const statusColumn =
        document.createElement("div");


    const status =
        document.createElement("span");

    status.className =
        "status-badge indexed";

    status.textContent =
        documentData.status || "Indexed";


    statusColumn.appendChild(status);


    // PAGES
    const pagesColumn =
        document.createElement("div");

    pagesColumn.className =
        "document-meta";

    pagesColumn.textContent =
        `${documentData.pages || 0} pages`;


    // SIZE
    const sizeColumn =
        document.createElement("div");

    sizeColumn.className =
        "document-meta";

    sizeColumn.textContent =
        documentData.size || "—";


    // BUILD ROW
   

    row.appendChild(fileColumn);
    row.appendChild(statusColumn);
    row.appendChild(pagesColumn);
    row.appendChild(sizeColumn);


    // Add newest document at top
    documentList.prepend(row);

    console.log(
        "Added document to Knowledge Base:",
        documentData
    );
}


// FILE SIZE


function formatFileSize(bytes) {
    if (!bytes || bytes <= 0) {
        return "—";
    }

    const units = [
        "B",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );

    const safeIndex =
        Math.min(
            index,
            units.length - 1
        );

    const size =
        bytes /
        Math.pow(
            1024,
            safeIndex
        );

    return `${size.toFixed(
        safeIndex === 0 ? 0 : 1
    )} ${units[safeIndex]}`;
}


// UPLOAD STATUS


function setUploadStatus(
    message,
    type = ""
) {
    const status =
        getElement("uploadStatus");

    if (!status) {
        return;
    }

    status.textContent =
        message;

    status.classList.remove(
        "success",
        "error",
        "status-success",
        "status-error"
    );

    if (type === "success") {
        status.classList.add("success");

    } else if (type === "error") {
        status.classList.add("error");
    }
}



//   SHOW DOCUMENT


function showDocument(data) {
    const card =
        getElement("documentCard");

    const name =
        getElement("documentName");

    const info =
        getElement("documentInfo");

    if (!card) {
        return;
    }

    card.classList.remove("hidden");

    if (name) {
        name.textContent =
            data.document ||
            "Uploaded PDF";
    }

    if (info) {
        const pages =
            data.pages || 0;

        const chunks =
            data.chunks || 0;

        info.textContent =
            `${pages} pages • ${chunks} chunks indexed`;
    }
}


// RESET DOCUMENT


function resetDocument() {
    currentDocumentId = null;
    currentDocumentName = "";

    currentAssistantMessage = null;
    currentAssistantRawText = "";

    isSending = false;

    updateQuestionState();
    updateClearButton();
}


// INITIALIZE


document.addEventListener(
    "DOMContentLoaded",
    function () {
        console.log(
            "===================================="
        );

        console.log(
            "Realtime RAG frontend started."
        );

        console.log(
            "API:",
            API_BASE_URL
        );

        console.log(
            "WebSocket:",
            WEBSOCKET_URL
        );

        console.log(
            "===================================="
        );


        /* File picker */
        setupFileInput();


        /* Chat input */
        setupChatInput();


        /* WebSocket */
        connectWebSocket();


        /* Initial state */
        updateQuestionState();
        updateClearButton();
    }
);


// BROWSER ONLINE


window.addEventListener(
    "online",
    function () {
        console.log(
            "Browser is online."
        );

        connectWebSocket();
    }
);


// BROWSER OFFLINE


window.addEventListener(
    "offline",
    function () {
        console.log(
            "Browser is offline."
        );

        setConnectionStatus(
            false,
            "Offline"
        );

        updateQuestionState();
    }
);