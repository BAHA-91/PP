import React, { useState } from 'react';
import "./App.css"


const QuestionInput = () => {
  const [question, setQuestion] = useState('');
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setFileName(droppedFile.name);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    if (!file) {
      alert("Please upload a PDF file before submitting.");
      return;
    }
  
    if (!question) {
      alert("Please enter a question.");
      return;
    }
  
    const formData = new FormData();
    formData.append("file", file);
  
    try {
      
      const uploadRes = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });
  
      const uploadData = await uploadRes.json();
      if (!uploadRes.ok) {
        throw new Error(uploadData.error || "File upload failed");
      }
  
      console.log(" Upload success:", uploadData.message);
  
      
      console.log("📤 Sending question to /ask:", question);
  
      const askRes = await fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }), 
      });
  
      const askData = await askRes.json();
      console.log(" Answer received:", askData.answer);
  
      
      setAnswer(askData.answer);
    } catch (error) {
      console.error(" Error:", error.message);
    }
  };
  
  

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-8 mx-4 bg-white rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl">
        <h2 className="mb-6 text-2xl font-semibold text-center text-purple-800">Ask a Question</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Question Input */}
          <div className="mb-6">
            <label htmlFor="question" className="block mb-2 text-sm font-medium text-gray-700">
              Your Question
            </label>
            <textarea
              id="question"
              rows="4"
              value={question}
              onChange={handleQuestionChange}
              className="w-full px-4 py-3 text-gray-700 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              placeholder="What would you like to know about your document?"
              required
            ></textarea>
          </div>
          
          {/* File Upload */}
          <div className="mb-6">
            <label className="block mb-2 text-sm font-medium text-gray-700">
              Upload PDF Document
            </label>
            <div
              className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-purple-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center justify-center">
                <svg
                  className="w-10 h-10 mb-3 text-purple-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  ></path>
                </svg>
                <p className="mb-1 text-sm text-gray-600">
                  {fileName ? fileName : 'Drag & drop your PDF or click to browse'}
                </p>
                <p className="text-xs text-gray-500">PDF files only</p>
              </div>
            </div>
            {file && (
              <p className="mt-2 text-sm text-purple-600">
                File ready to upload
              </p>
            )}
          </div>
          
          {/* Submit Button */}
          <button
            type="submit"
            className="w-full px-6 py-3 text-white bg-purple-600 rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-4 focus:ring-purple-300 transition-all duration-300 transform hover:-translate-y-1"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
};

export default QuestionInput;