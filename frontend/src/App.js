 

// //import React, { useState } from 'react';
// import React, { useState, useEffect } from 'react';

// const FollowupQuestionsPopup = ({ 
//   sessionId, 
//   questions = [], 
//   onClose, 
//   onSubmit,
//   isOpen = true 
// }) => {
//   const [answers, setAnswers] = useState(Array(questions.length).fill(''));
//   const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
//   const [isSubmitting, setIsSubmitting] = useState(false);

//   const handleAnswerChange = (index, value) => {
//     const newAnswers = [...answers];
//     newAnswers[index] = value;
//     setAnswers(newAnswers);
//   };

//   const handleNext = () => {
//     if (currentQuestionIndex < questions.length - 1) {
//       setCurrentQuestionIndex(currentQuestionIndex + 1);
//     }
//   };

//   const handlePrevious = () => {
//     if (currentQuestionIndex > 0) {
//       setCurrentQuestionIndex(currentQuestionIndex - 1);
//     }
//   };

//   const handleSubmit = async () => {
//     const allAnswered = answers.every(answer => answer.trim());
//     if (!allAnswered) {
//       alert('Please answer all questions before submitting.');
//       return;
//     }

//     setIsSubmitting(true);
//     try {
//       await onSubmit(answers);
//       onClose();
//     } catch (error) {
//       console.error('Error submitting answers:', error);
//       alert('Failed to submit answers. Please try again.');
//     } finally {
//       setIsSubmitting(false);
//     }
//   };


// // ADD THIS SECTION - Authentication utility functions for LogBook JWT integration
// const AuthUtils = {
//   // Get JWT token from various possible locations
//   getToken: () => {
//     // Try localStorage first (most common for SPAs)
//     let token = localStorage.getItem('logbook_token') || localStorage.getItem('token');
    
//     // Try sessionStorage
//     if (!token) {
//       token = sessionStorage.getItem('logbook_token') || sessionStorage.getItem('token');
//     }
    
//     // Try cookies as fallback
//     if (!token) {
//       token = AuthUtils.getCookie('logbook_token');
//     }
    
//     return token;
//   },

//   // Get cookie by name
//   getCookie: (name) => {
//     const value = `; ${document.cookie}`;
//     const parts = value.split(`; ${name}=`);
//     if (parts.length === 2) return parts.pop().split(';').shift();
//     return null;
//   },

//   // Check if user is authenticated
//   isAuthenticated: () => {
//     const token = AuthUtils.getToken();
//     if (!token) return false;
    
//     try {
//       // Basic JWT validation - check if not expired
//       const payload = JSON.parse(atob(token.split('.')[1]));
//       const currentTime = Date.now() / 1000;
//       return payload.exp > currentTime;
//     } catch (error) {
//       console.error('Invalid token format:', error);
//       return false;
//     }
//   },

//   // Get authentication headers for API calls
//   getAuthHeaders: () => {
//     const token = AuthUtils.getToken();
    
//     if (!token) {
//       console.warn('No authentication token found');
//       // In real integration, redirect to LogBook login page
//       // window.location.href = '/login';
//       return {
//         'Content-Type': 'application/json',
//         'Accept': 'application/json'
//       };
//     }
    
//     return {
//       'Authorization': `Bearer ${token}`,
//       'Content-Type': 'application/json',
//       'Accept': 'application/json'
//     };
//   },

//   // Redirect to login (to be integrated with LogBook's login page)
//   redirectToLogin: () => {
//     console.log('Redirecting to LogBook login...');
//     // In real integration:
//     // window.location.href = '/login';
//     alert('Please log in through the LogBook system first.');
//   },

//   // Logout function
//   logout: () => {
//     localStorage.removeItem('logbook_token');
//     localStorage.removeItem('token');
//     sessionStorage.removeItem('logbook_token');
//     sessionStorage.removeItem('token');
//     // In real integration, also call LogBook logout endpoint
//     window.location.href = '/login';
//   }
// };

// // ADD THIS COMPONENT - Authentication Guard Component
// const AuthGuard = ({ children }) => {
//   const [isAuthenticated, setIsAuthenticated] = useState(false);
//   const [isChecking, setIsChecking] = useState(true);

//   useEffect(() => {
//     const checkAuth = () => {
//       const authenticated = AuthUtils.isAuthenticated();
//       setIsAuthenticated(authenticated);
//       setIsChecking(false);
      
//       if (!authenticated) {
//         console.log('User not authenticated, showing login prompt');
//       }
//     };

//     checkAuth();
    
//     // Check authentication status periodically
//     const interval = setInterval(checkAuth, 60000); // Check every minute
    
//     return () => clearInterval(interval);
//   }, []);

//   if (isChecking) {
//     return (
//       <div style={{
//         minHeight: '100vh',
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         backgroundColor: '#f5f7fa'
//       }}>
//         <div style={{ textAlign: 'center' }}>
//           <div style={{ 
//             fontSize: '24px', 
//             marginBottom: '16px',
//             color: '#2196F3'
//           }}>
//             🔐
//           </div>
//           <p style={{ color: '#666' }}>Checking authentication...</p>
//         </div>
//       </div>
//     );
//   }

//   if (!isAuthenticated) {
//     return (
//       <div style={{
//         minHeight: '100vh',
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         backgroundColor: '#f5f7fa'
//       }}>
//         <div style={{
//           backgroundColor: 'white',
//           borderRadius: '16px',
//           padding: '48px',
//           textAlign: 'center',
//           boxShadow: '0 8px 20px rgba(0,0,0,0.1)',
//           maxWidth: '400px',
//           width: '90%'
//         }}>
//           <div style={{
//             width: '80px',
//             height: '80px',
//             backgroundColor: '#ff9800',
//             borderRadius: '20px',
//             display: 'flex',
//             alignItems: 'center',
//             justifyContent: 'center',
//             margin: '0 auto 24px auto',
//             fontSize: '40px',
//             color: 'white'
//           }}>
//             🔐
//           </div>
          
//           <h2 style={{
//             color: '#333',
//             fontSize: '24px',
//             fontWeight: '600',
//             margin: '0 0 16px 0'
//           }}>
//             Authentication Required
//           </h2>
          
//           <p style={{
//             color: '#666',
//             fontSize: '16px',
//             lineHeight: '1.6',
//             margin: '0 0 32px 0'
//           }}>
//             Please log in through the LogBook system to access the Daily Activity Log.
//           </p>
          
//           <button
//             onClick={AuthUtils.redirectToLogin}
//             style={{
//               padding: '12px 32px',
//               backgroundColor: '#2196F3',
//               color: 'white',
//               border: 'none',
//               borderRadius: '8px',
//               cursor: 'pointer',
//               fontSize: '16px',
//               fontWeight: '600'
//             }}
//           >
//             Go to Login
//           </button>
//         </div>
//       </div>
//     );
//   }

//   return children;
// };
// //end new

//   const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
//   const answeredCount = answers.filter(answer => answer.trim()).length;

//   if (!isOpen || questions.length === 0) {
//     return null;
//   }

//   return (
//     <div style={{
//       position: 'fixed',
//       top: 0,
//       left: 0,
//       right: 0,
//       bottom: 0,
//       backgroundColor: 'rgba(0, 0, 0, 0.5)',
//       display: 'flex',
//       alignItems: 'center',
//       justifyContent: 'center',
//       zIndex: 1000
//     }}>
//       <div style={{
//         backgroundColor: 'white',
//         borderRadius: '8px',
//         padding: '32px',
//         width: '90%',
//         maxWidth: '600px',
//         maxHeight: '80vh',
//         overflow: 'auto'
//       }}>
//         {/* Header */}
//         <div style={{ 
//           display: 'flex', 
//           justifyContent: 'space-between', 
//           alignItems: 'center',
//           marginBottom: '24px'
//         }}>
//           <h2 style={{ 
//             margin: 0, 
//             fontSize: '24px',
//             fontWeight: 'bold',
//             color: '#333'
//           }}>
//             Follow-up Questions
//           </h2>
//           {/* <button
//             onClick={onClose}
//             style={{
//               background: 'none',
//               border: 'none',
//               fontSize: '24px',
//               cursor: 'pointer',
//               color: '#666'
//             }}
//           >
//             ×
//           </button> */}
//         </div>

//         {/* Progress Bar */}
//         <div style={{
//           backgroundColor: '#e0e0e0',
//           borderRadius: '10px',
//           height: '8px',
//           marginBottom: '16px'
//         }}>
//           <div
//             style={{
//               backgroundColor: '#4CAF50',
//               height: '100%',
//               borderRadius: '10px',
//               width: `${progress}%`,
//               transition: 'width 0.3s ease'
//             }}
//           />
//         </div>

//         <div style={{ 
//           textAlign: 'center',
//           marginBottom: '24px',
//           fontSize: '14px',
//           color: '#666'
//         }}>
//           Question {currentQuestionIndex + 1} of {questions.length} ({answeredCount} answered)
//         </div>

//         {/* Current Question */}
//         <div style={{ marginBottom: '24px' }}>
//           <h3 style={{
//             margin: '0 0 16px 0',
//             fontSize: '18px',
//             color: '#333'
//           }}>
//             {questions[currentQuestionIndex]}
//           </h3>
          
//           <textarea
//             value={answers[currentQuestionIndex]}
//             onChange={(e) => handleAnswerChange(currentQuestionIndex, e.target.value)}
//             placeholder="Type your answer here..."
//             rows={6}
//             style={{
//               width: '100%',
//               padding: '12px',
//               border: '1px solid #ccc',
//               borderRadius: '4px',
//               fontSize: '16px',
//               resize: 'vertical',
//               boxSizing: 'border-box'
//             }}
//           />
//         </div>

//         {/* Navigation */}
//         <div style={{
//           display: 'flex',
//           justifyContent: 'space-between',
//           alignItems: 'center'
//         }}>
//           <button
//             onClick={handlePrevious}
//             disabled={currentQuestionIndex === 0}
//             style={{
//               padding: '10px 20px',
//               backgroundColor: currentQuestionIndex === 0 ? '#f5f5f5' : '#fff',
//               color: currentQuestionIndex === 0 ? '#999' : '#333',
//               border: '1px solid #ccc',
//               borderRadius: '4px',
//               cursor: currentQuestionIndex === 0 ? 'not-allowed' : 'pointer'
//             }}
//           >
//             Previous
//           </button>

//           {currentQuestionIndex === questions.length - 1 ? (
//             <button
//               onClick={handleSubmit}
//               disabled={isSubmitting}
//               style={{
//                 padding: '10px 24px',
//                 backgroundColor: isSubmitting ? '#ccc' : '#4CAF50',
//                 color: 'white',
//                 border: 'none',
//                 borderRadius: '4px',
//                 cursor: isSubmitting ? 'not-allowed' : 'pointer',
//                 fontSize: '16px'
//               }}
//             >
//               {isSubmitting ? 'Submitting...' : 'Submit All Answers'}
//             </button>
//           ) : (
//             <button
//               onClick={handleNext}
//               style={{
//                 padding: '10px 20px',
//                 backgroundColor: '#2196F3',
//                 color: 'white',
//                 border: 'none',
//                 borderRadius: '4px',
//                 cursor: 'pointer'
//               }}
//             >
//               Next
//             </button>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// // Follow-up Redirect Screen Component
// const FollowupRedirectScreen = ({ 
//   userId, 
//   tempWorkUpdateId, 
//   onStartFollowup
// }) => {
//   const [isStarting, setIsStarting] = useState(false);

//   const handleStartFollowup = async () => {
//     setIsStarting(true);
//     try {
//       await onStartFollowup();
//     } catch (error) {
//       console.error('Error starting follow-up:', error);
//       alert('Failed to start follow-up session. Please try again.');
//     } finally {
//       setIsStarting(false);
//     }
//   };

//   return (
//     <div style={{
//       position: 'fixed',
//       top: 0,
//       left: 0,
//       right: 0,
//       bottom: 0,
//       backgroundColor: 'rgba(0, 0, 0, 0.5)',
//       display: 'flex',
//       alignItems: 'center',
//       justifyContent: 'center',
//       zIndex: 1000
//     }}>
//       <div style={{
//         backgroundColor: 'white',
//         borderRadius: '8px',
//         padding: '40px',
//         width: '50%',
//         maxWidth: '500px',
//         textAlign: 'center'
//       }}>
//         {/* Success Icon */}
//         {/* <div style={{
//           width: '60px',
//           height: '60px',
//           backgroundColor: '#2196F3',
//           borderRadius: '50%',
//           display: 'flex',
//           alignItems: 'center',
//           justifyContent: 'center',
//           margin: '0 auto 24px auto',
//           fontSize: '40px',
//           color: 'white'
//         }}>
          
//         </div> */}

        

//         <p style={{
//           color: '#666',
//           fontSize: '16px',
//           lineHeight: '1.5',
//           margin: '0 0 32px 0'
//         }}>
//           Please complete the required follow-up to submit your work update.
//         </p>

//         <button
//           onClick={handleStartFollowup}
//           disabled={isStarting}
//           style={{
//             padding: '12px 32px',
//             backgroundColor: isStarting ? '#ccc' : '#2196F3',
//             color: 'white',
//             border: 'none',
//             borderRadius: '4px',
//             cursor: isStarting ? 'not-allowed' : 'pointer',
//             fontSize: '16px',
//             fontWeight: 'bold'
//           }}
//         >
//           {isStarting ? 'Starting...' : "Let's Go"}
//         </button>
//       </div>
//     </div>
//   );
// };

// // ADD THIS - Available task stacks
// const taskStacks = [
//   'Frontend Development',
//   'Backend Development', 
//   'Mobile Development',
//   'DevOps & Infrastructure',
//   'UI/UX Design',
//   'Quality Assurance',
//   'Data Science',
//   'Machine Learning',
//   'Product Management',
//   'Business Analysis'
// ];


// // Main Work Update System Component
// const WorkUpdateSystem = () => {
//   //const [userId, setUserId] = useState('');
//   //const [workStatus, setWorkStatus] = useState('working'); // 'working', 'work from home', or 'onLeave'
//   //const [description, setDescription] = useState('');
//   const [status, setStatus] = useState('working'); // Change from workStatus
//   const [taskStack, setTaskStack] = useState(''); // ADD THIS
//   const [tasksCompleted, setTasksCompleted] = useState(''); // Change from description
//   const [challengesFaced, setChallengesFaced] = useState('');
//   const [plansForTomorrow, setPlansForTomorrow] = useState('');
  
//   // State for follow-up flow
//   const [showFollowupRedirect, setShowFollowupRedirect] = useState(false);
//   const [showFollowupQuestions, setShowFollowupQuestions] = useState(false);
//   const [tempWorkUpdateId, setTempWorkUpdateId] = useState(null); // Changed to temp ID
//   const [followupData, setFollowupData] = useState(null);

//   const handleSubmitWorkUpdate = async () => {
//     // Validation
//     if (!userId.trim()) {
//       alert('Please enter your User ID');
//       return;
//     }

//     // If working or work from home, require description. If on leave, description is optional
//     if ((workStatus === 'working' || workStatus === 'work from home') && !description.trim()) {
//       alert('Please enter your work description');
//       return;
//     }

//     try {
//       // Build payload based on work status
//       let workUpdateData;
      
//       if (workStatus === 'onLeave') {
//         // On leave submission - minimal data
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "on_leave",
//           "description": description.trim() || "On Leave",
//           "challenges": "",
//           "plans": ""
//         };
//       } else if (workStatus === 'work from home') {
//         // Work from home submission - treat as working
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "work_from_home",
//           "description": description.trim(),
//           "challenges": challengesFaced.trim() || "",
//           "plans": plansForTomorrow.trim() || ""
//         };
//       } else {
//         // Working submission - full data
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "working",
//           "description": description.trim(),
//           "challenges": challengesFaced.trim() || "",
//           "plans": plansForTomorrow.trim() || ""
//         };
//       }

//       console.log('Submitting work update:', workUpdateData);

//       // STEP 1: Save work update only
//       const response = await fetch('http://localhost:8000/api/work-updates', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'Accept': 'application/json'
//         },
//         body: JSON.stringify(workUpdateData)
//       });

//       console.log('Response status:', response.status);

//       if (!response.ok) {
//         const errorText = await response.text();
//         console.error('Raw error response:', errorText);
//         throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
//       }

//       const result = await response.json();
//       console.log('Work update result:', result);

//       if (workStatus === 'onLeave') {
//         // On leave - work update saved permanently, no follow-up needed
//         alert('Your leave status has been submitted successfully!');
//         resetForm();
//       } else if (workStatus === 'working' || workStatus === 'work from home') {
//         // Working or work from home - work update saved to temp, need follow-up to finalize
//         setTempWorkUpdateId(result.tempWorkUpdateId);
//         setShowFollowupRedirect(true);
//       }

//     } catch (error) {
//       console.error('Error submitting work update:', error);
//       alert('Failed to submit work update: ' + error.message);
//     }
//   };

//   const handleStartFollowup = async () => {
//     try {
//       console.log('Starting follow-up session...');
      
//       // STEP 2: Start follow-up session (using temp work update ID)
//       const response = await fetch(`http://localhost:8000/api/followups/start?temp_work_update_id=${tempWorkUpdateId}&user_id=${userId}`, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         }
//       });

//       if (!response.ok) {
//         throw new Error(`HTTP error! status: ${response.status}`);
//       }

//       const result = await response.json();
//       console.log('Follow-up session started:', result);

//       // Set follow-up data and show questions popup
//       setFollowupData({
//         sessionId: result.sessionId,
//         questions: result.questions
//       });

//       // Hide redirect screen and show questions popup
//       setShowFollowupRedirect(false);
//       setShowFollowupQuestions(true);

//     } catch (error) {
//       console.error('Error starting follow-up:', error);
//       throw new Error('Failed to start follow-up session: ' + error.message);
//     }
//   };

//   const handleFollowupSubmit = async (answers) => {
//     try {
//       console.log('Submitting followup answers:', answers);
      
//       // Call your FastAPI backend to complete the follow-up session
//       const response = await fetch(`http://localhost:8000/api/followup/${followupData.sessionId}/complete`, {
//         method: 'PUT',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//           answers: answers
//         })
//       });

//       if (!response.ok) {
//         throw new Error(`HTTP error! status: ${response.status}`);
//       }

//       const result = await response.json();
//       console.log('Follow-up completed:', result);
      
//       alert('Follow-up questions completed successfully!');
      
//       // Reset form and close popups
//       resetForm();
//       setShowFollowupQuestions(false);
      
//     } catch (error) {
//       console.error('Error submitting followup:', error);
//       throw new Error('Failed to submit follow-up answers: ' + error.message);
//     }
//   };

//   const resetForm = () => {
//     setUserId('');
//     setDescription('');
//     setChallengesFaced('');
//     setPlansForTomorrow('');
//     setWorkStatus('working');
//     setTempWorkUpdateId(null); // Reset temp ID
//     setFollowupData(null);
//   };

//   const handleCloseFollowupRedirect = () => {
//     setShowFollowupRedirect(false);
//     resetForm();
//   };

//   const handleCloseFollowupQuestions = () => {
//     setShowFollowupQuestions(false);
//     resetForm();
//   };

//   return (
//     <div style={{
//       minHeight: '100vh',
//       backgroundColor: '#f5f5f5',
//       padding: '40px 20px'
//     }}>
//       <div style={{
//         maxWidth: '600px',
//         margin: '0 auto',
//         backgroundColor: 'white',
//         padding: '40px',
//         borderRadius: '8px',
//         boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
//       }}>
//         <div style={{ textAlign: 'center', marginBottom: '32px' }}>
//           <h1 style={{
//             fontSize: '36px',
//             fontWeight: 'bold',
//             color: '#4A90E2',
//             margin: '0 0 8px 0'
//           }}>
//             Work Update System
//           </h1>
//           <p style={{
//             color: '#666',
//             fontSize: '16px',
//             margin: 0
//           }}>
//             Submit your daily work update and answer follow-up questions
//           </p>
//         </div>

//         {/* User ID */}
//         <div style={{ marginBottom: '24px' }}>
//           <label style={{
//             display: 'block',
//             fontWeight: 'bold',
//             marginBottom: '8px',
//             color: '#333'
//           }}>
//             User ID *
//           </label>
//           <input
//             type="text"
//             value={userId}
//             onChange={(e) => setUserId(e.target.value)}
//             placeholder="Enter your user ID"
//             style={{
//               width: '100%',
//               padding: '12px',
//               border: '1px solid #ddd',
//               borderRadius: '4px',
//               fontSize: '16px',
//               boxSizing: 'border-box'
//             }}
//           />
//         </div>

//         {/* Work Status Radio Buttons */}
//         <div style={{ marginBottom: '24px' }}>
//           <label style={{
//             display: 'block',
//             fontWeight: 'bold',
//             marginBottom: '12px',
//             color: '#333'
//           }}>
//             Status *
//           </label>
//           <div style={{
//             display: 'flex',
//             gap: '20px',
//             marginBottom: '8px'
//           }}>
//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'working' ? '#4A90E2' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'working' ? '#f0f8ff' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="working"
//                 checked={workStatus === 'working'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'working' ? 'bold' : 'normal' }}>
//                 Working
//               </span>
//             </label>

//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'work from home' ? '#4A90E2' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'work from home' ? '#f0f8ff' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="work from home"
//                 checked={workStatus === 'work from home'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'work from home' ? 'bold' : 'normal' }}>
//                 Work From Home
//               </span>
//             </label>

//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'onLeave' ? '#FF9800' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'onLeave' ? '#fff8e1' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="onLeave"
//                 checked={workStatus === 'onLeave'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'onLeave' ? 'bold' : 'normal' }}>
//                 On Leave
//               </span>
//             </label>
//           </div>
//         </div>

//         {/* Work Description - Only show when working */}
//         {(workStatus === 'working' || workStatus === 'work from home') && (
//           <div style={{ marginBottom: '24px' }}>
//             <label style={{
//               display: 'block',
//               fontWeight: 'bold',
//               marginBottom: '8px',
//               color: '#333'
//             }}>
//               Work Description *
//             </label>
//             <textarea
//               value={description}
//               onChange={(e) => setDescription(e.target.value)}
//               placeholder="What did you accomplish today? Be specific..."
//               rows={4}
//               style={{
//                 width: '100%',
//                 padding: '12px',
//                 border: '1px solid #ddd',
//                 borderRadius: '4px',
//                 fontSize: '16px',
//                 resize: 'vertical',
//                 boxSizing: 'border-box'
//               }}
//             />
//           </div>
//         )}

//         {/* Show additional fields only when working */}
//         {(workStatus === 'working' || workStatus === 'work from home') && (
//           <>
//             {/* Challenges Faced - Optional */}
//             <div style={{ marginBottom: '24px' }}>
//               <label style={{
//                 display: 'block',
//                 fontWeight: 'bold',
//                 marginBottom: '8px',
//                 color: '#333'
//               }}>
//                 Challenges Faced
//               </label>
//               <textarea
//                 value={challengesFaced}
//                 onChange={(e) => setChallengesFaced(e.target.value)}
//                 placeholder="Any challenges or difficulties you encountered..."
//                 rows={3}
//                 style={{
//                   width: '100%',
//                   padding: '12px',
//                   border: '1px solid #ddd',
//                   borderRadius: '4px',
//                   fontSize: '16px',
//                   resize: 'vertical',
//                   boxSizing: 'border-box'
//                 }}
//               />
//             </div>

//             {/* Plans for Tomorrow - Optional */}
//             <div style={{ marginBottom: '32px' }}>
//               <label style={{
//                 display: 'block',
//                 fontWeight: 'bold',
//                 marginBottom: '8px',
//                 color: '#333'
//               }}>
//                 Plans for Tomorrow
//               </label>
//               <textarea
//                 value={plansForTomorrow}
//                 onChange={(e) => setPlansForTomorrow(e.target.value)}
//                 placeholder="What will you focus on tomorrow..."
//                 rows={3}
//                 style={{
//                   width: '100%',
//                   padding: '12px',
//                   border: '1px solid #ddd',
//                   borderRadius: '4px',
//                   fontSize: '16px',
//                   resize: 'vertical',
//                   boxSizing: 'border-box'
//                 }}
//               />
//             </div>
//           </>
//         )}

//         {/* Submit Button */}
//         <button
//           onClick={handleSubmitWorkUpdate}
//           style={{
//             width: '100%',
//             padding: '16px',
//             backgroundColor: workStatus === 'onLeave' ? '#FF9800' : '#4A90E2',
//             color: 'white',
//             border: 'none',
//             borderRadius: '4px',
//             fontSize: '18px',
//             fontWeight: 'bold',
//             cursor: 'pointer'
//           }}
//         >
//           {workStatus === 'onLeave' ? 'Submit Leave Status' : 'Submit Work Update'}
//         </button>

//         {/* Status indicator */}
//         {workStatus === 'onLeave' && (
//           <div style={{
//             marginTop: '16px',
//             padding: '12px',
//             backgroundColor: '#fff3cd',
//             border: '1px solid #ffeaa7',
//             borderRadius: '4px',
//             color: '#856404',
//             fontSize: '14px',
//             textAlign: 'center'
//           }}>
//             ℹ️ No further details needed for leave days
//           </div>
//         )}
//       </div>

//       {/* Follow-up Redirect Screen */}
//       {showFollowupRedirect && (
//         <FollowupRedirectScreen
//           userId={userId}
//           tempWorkUpdateId={tempWorkUpdateId}
//           onStartFollowup={handleStartFollowup}
//         />
//       )}

//       {/* Follow-up Questions Popup */}
//       {showFollowupQuestions && followupData && (
//         <FollowupQuestionsPopup
//           sessionId={followupData.sessionId}
//           questions={followupData.questions}
//           isOpen={showFollowupQuestions}
//           onClose={handleCloseFollowupQuestions}
//           onSubmit={handleFollowupSubmit}
//         />
//       )}
//     </div>
//   );
// };

// export default WorkUpdateSystem;




import React, { useState, useEffect } from 'react';

// Authentication utility functions for LogBook JWT integration
const AuthUtils = {
  // Get JWT token from various possible locations
  getToken: () => {
    // Try localStorage first (most common for SPAs)
    let token = localStorage.getItem('logbook_token') || localStorage.getItem('token');
    
    // Try sessionStorage
    if (!token) {
      token = sessionStorage.getItem('logbook_token') || sessionStorage.getItem('token');
    }
    
    // Try cookies as fallback
    if (!token) {
      token = AuthUtils.getCookie('logbook_token');
    }
    
    return token;
  },

  // Get cookie by name
  getCookie: (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    const token = AuthUtils.getToken();
    if (!token) return false;
    
    try {
      // Basic JWT validation - check if not expired
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Invalid token format:', error);
      return false;
    }
  },

  // Get authentication headers for API calls
  getAuthHeaders: () => {
    const token = AuthUtils.getToken();
    
    if (!token) {
      console.warn('No authentication token found');
      // For development/testing, still return basic headers
      return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        // Fallback headers for testing
        'X-Intern-ID': '507f1f77bcf86cd799439011',
        'X-Intern-Email': 'intern@talenthub.com'
      };
    }
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  },

  // Redirect to login (to be integrated with LogBook's login page)
  redirectToLogin: () => {
    console.log('Redirecting to LogBook login...');
    // In real integration:
    // window.location.href = '/login';
    alert('Please log in through the LogBook system first.');
  },

  // Logout function
  logout: () => {
    localStorage.removeItem('logbook_token');
    localStorage.removeItem('token');
    sessionStorage.removeItem('logbook_token');
    sessionStorage.removeItem('token');
    // In real integration, also call LogBook logout endpoint
    window.location.href = '/login';
  }
};

// Follow-up Questions Popup Component
const FollowupQuestionsPopup = ({ 
  sessionId, 
  questions = [], 
  onClose, 
  onSubmit,
  isOpen = true 
}) => {
  const [answers, setAnswers] = useState(Array(questions.length).fill(''));
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnswerChange = (index, value) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = async () => {
    const allAnswered = answers.every(answer => answer.trim());
    if (!allAnswered) {
      alert('Please answer all questions before submitting.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(answers);
      onClose();
    } catch (error) {
      console.error('Error submitting answers:', error);
      if (error.message.includes('401') || error.message.includes('Authentication')) {
        AuthUtils.redirectToLogin();
      } else {
        alert('Failed to submit answers. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
  const answeredCount = answers.filter(answer => answer.trim()).length;

  if (!isOpen || questions.length === 0) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '32px',
        width: '90%',
        maxWidth: '650px',
        maxHeight: '85vh',
        overflow: 'auto',
        boxShadow: '0 10px 25px rgba(0,0,0,0.15)'
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '24px',
          paddingBottom: '16px',
          borderBottom: '2px solid #f0f0f0'
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '28px',
            fontWeight: '600',
            color: '#2196F3',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{ 
              backgroundColor: '#2196F3',
              color: 'white',
              borderRadius: '8px',
              padding: '8px',
              fontSize: '20px'
            }}>
              🤖
            </span>
            AI Follow-up Questions
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '28px',
              cursor: 'pointer',
              color: '#999',
              padding: '4px'
            }}
          >
            ×
          </button>
        </div>

        {/* Progress Bar */}
        <div style={{
          backgroundColor: '#e8f4fd',
          borderRadius: '12px',
          height: '12px',
          marginBottom: '16px',
          overflow: 'hidden'
        }}>
          <div
            style={{
              backgroundColor: '#2196F3',
              height: '100%',
              borderRadius: '12px',
              width: `${progress}%`,
              transition: 'width 0.3s ease'
            }}
          />
        </div>

        <div style={{ 
          textAlign: 'center',
          marginBottom: '24px',
          fontSize: '16px',
          color: '#666',
          fontWeight: '500'
        }}>
          Question {currentQuestionIndex + 1} of {questions.length} • {answeredCount} answered
        </div>

        {/* Current Question */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{
            backgroundColor: '#f8f9fa',
            padding: '20px',
            borderRadius: '10px',
            marginBottom: '20px',
            borderLeft: '4px solid #2196F3'
          }}>
            <h3 style={{
              margin: '0 0 8px 0',
              fontSize: '18px',
              color: '#333',
              lineHeight: '1.4'
            }}>
              {questions[currentQuestionIndex]}
            </h3>
          </div>
          
          <textarea
            value={answers[currentQuestionIndex]}
            onChange={(e) => handleAnswerChange(currentQuestionIndex, e.target.value)}
            placeholder="Type your detailed answer here..."
            rows={6}
            style={{
              width: '100%',
              padding: '16px',
              border: '2px solid #e0e0e0',
              borderRadius: '8px',
              fontSize: '16px',
              resize: 'vertical',
              boxSizing: 'border-box',
              fontFamily: 'inherit',
              lineHeight: '1.5',
              transition: 'border-color 0.2s ease'
            }}
            onFocus={(e) => e.target.style.borderColor = '#2196F3'}
            onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
          />
          
          <div style={{
            marginTop: '8px',
            fontSize: '14px',
            color: answers[currentQuestionIndex].length > 20 ? '#4CAF50' : '#ff9800'
          }}>
            {answers[currentQuestionIndex].length} characters
            {answers[currentQuestionIndex].length < 20 && ' (aim for detailed responses)'}
          </div>
        </div>

        {/* Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '16px',
          borderTop: '1px solid #f0f0f0'
        }}>
          <button
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            style={{
              padding: '12px 24px',
              backgroundColor: currentQuestionIndex === 0 ? '#f5f5f5' : 'white',
              color: currentQuestionIndex === 0 ? '#999' : '#333',
              border: '2px solid #e0e0e0',
              borderRadius: '8px',
              cursor: currentQuestionIndex === 0 ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
          >
            ← Previous
          </button>

          {currentQuestionIndex === questions.length - 1 ? (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || answeredCount < questions.length}
              style={{
                padding: '12px 32px',
                backgroundColor: isSubmitting || answeredCount < questions.length ? '#cccccc' : '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: isSubmitting || answeredCount < questions.length ? 'not-allowed' : 'pointer',
                fontSize: '16px',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
            >
              {isSubmitting ? 'Submitting...' : `Submit All (${answeredCount}/${questions.length})`}
            </button>
          ) : (
            <button
              onClick={handleNext}
              style={{
                padding: '12px 24px',
                backgroundColor: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
            >
              Next →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Follow-up Redirect Screen Component
const FollowupRedirectScreen = ({ 
  tempWorkUpdateId, 
  onStartFollowup
}) => {
  const [isStarting, setIsStarting] = useState(false);

  const handleStartFollowup = async () => {
    setIsStarting(true);
    try {
      await onStartFollowup();
    } catch (error) {
      console.error('Error starting follow-up:', error);
      if (error.message.includes('401') || error.message.includes('Authentication')) {
        AuthUtils.redirectToLogin();
      } else {
        alert('Failed to start follow-up session. Please try again.');
      }
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '48px',
        width: '90%',
        maxWidth: '500px',
        textAlign: 'center',
        boxShadow: '0 10px 25px rgba(0,0,0,0.15)'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          backgroundColor: '#2196F3',
          borderRadius: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 24px auto',
          fontSize: '40px',
          color: 'white'
        }}>
          🤖
        </div>

        <h2 style={{
          color: '#2196F3',
          fontSize: '28px',
          fontWeight: '600',
          margin: '0 0 16px 0'
        }}>
          AI Follow-up Required
        </h2>

        <p style={{
          color: '#666',
          fontSize: '18px',
          lineHeight: '1.6',
          margin: '0 0 32px 0'
        }}>
          Your work update needs AI validation before being saved to LogBook. 
          This will only take a few minutes.
        </p>

        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '16px',
          borderRadius: '8px',
          margin: '0 0 32px 0',
          fontSize: '14px',
          color: '#666'
        }}>
          <strong>What happens next:</strong>
          <br />• AI generates 3 personalized questions
          <br />• Answer based on your work today
          <br />• Your update gets saved to LogBook
        </div>

        <button
          onClick={handleStartFollowup}
          disabled={isStarting}
          style={{
            padding: '16px 40px',
            backgroundColor: isStarting ? '#cccccc' : '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: isStarting ? 'not-allowed' : 'pointer',
            fontSize: '18px',
            fontWeight: '600',
            transition: 'all 0.2s ease',
            minWidth: '180px'
          }}
        >
          {isStarting ? 'Starting AI...' : "Start Follow-up"}
        </button>
      </div>
    </div>
  );
};

// Success Screen Component
const SuccessScreen = ({ onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 3000);

    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '48px',
        width: '90%',
        maxWidth: '400px',
        textAlign: 'center',
        boxShadow: '0 10px 25px rgba(0,0,0,0.15)'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          backgroundColor: '#4CAF50',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 24px auto',
          fontSize: '40px',
          color: 'white'
        }}>
          ✓
        </div>

        <h2 style={{
          color: '#4CAF50',
          fontSize: '24px',
          fontWeight: '600',
          margin: '0 0 16px 0'
        }}>
          Successfully Submitted!
        </h2>

        <p style={{
          color: '#666',
          fontSize: '16px',
          margin: '0'
        }}>
          Your work update has been saved to LogBook.
        </p>
      </div>
    </div>
  );
};

// Authentication Guard Component
const AuthGuard = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const authenticated = AuthUtils.isAuthenticated();
      setIsAuthenticated(authenticated);
      setIsChecking(false);
      
      if (!authenticated) {
        console.log('User not authenticated, showing login prompt');
        // For development, we'll skip auth requirements
        setIsAuthenticated(true); // Remove this line in production
      }
    };

    checkAuth();
    
    // Check authentication status periodically
    const interval = setInterval(checkAuth, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, []);

  if (isChecking) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f7fa'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            fontSize: '24px', 
            marginBottom: '16px',
            color: '#2196F3'
          }}>
            🔐
          </div>
          <p style={{ color: '#666' }}>Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f7fa'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '48px',
          textAlign: 'center',
          boxShadow: '0 8px 20px rgba(0,0,0,0.1)',
          maxWidth: '400px',
          width: '90%'
        }}>
          <div style={{
            width: '80px',
            height: '80px',
            backgroundColor: '#ff9800',
            borderRadius: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px auto',
            fontSize: '40px',
            color: 'white'
          }}>
            🔐
          </div>
          
          <h2 style={{
            color: '#333',
            fontSize: '24px',
            fontWeight: '600',
            margin: '0 0 16px 0'
          }}>
            Authentication Required
          </h2>
          
          <p style={{
            color: '#666',
            fontSize: '16px',
            lineHeight: '1.6',
            margin: '0 0 32px 0'
          }}>
            Please log in through the LogBook system to access the Daily Activity Log.
          </p>
          
          <button
            onClick={AuthUtils.redirectToLogin}
            style={{
              padding: '12px 32px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '600'
            }}
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return children;
};

// Main LogBook Integration Component
const LogBookIntegration = () => {
  // Form state - updated to match LogBook structure
  const [status, setStatus] = useState('working'); // Changed from workStatus
  const [taskStack, setTaskStack] = useState(''); // New field for LogBook
  const [tasksCompleted, setTasksCompleted] = useState(''); // Changed from description
  const [challengesFaced, setChallengesFaced] = useState('');
  const [plansForTomorrow, setPlansForTomorrow] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Flow state
  const [showFollowupRedirect, setShowFollowupRedirect] = useState(false);
  const [showFollowupQuestions, setShowFollowupQuestions] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [tempWorkUpdateId, setTempWorkUpdateId] = useState(null);
  const [followupData, setFollowupData] = useState(null);

  // Available task stacks for LogBook integration
  const taskStacks = [
    'Frontend Development',
    'Backend Development', 
    'Mobile Development',
    'DevOps & Infrastructure',
    'UI/UX Design',
    'Quality Assurance',
    'Data Science',
    'Machine Learning',
    'Product Management',
    'Business Analysis'
  ];

  const validateForm = () => {
    if (!taskStack.trim()) {
      alert('Please select your task stack');
      return false;
    }

    if ((status === 'working' || status === 'wfh') && !tasksCompleted.trim()) {
      alert('Please describe what tasks you completed today');
      return false;
    }

    return true;
  };

  const handleSubmitLogbook = async () => {
    if (!validateForm()) return;

    // Check authentication before proceeding
    if (!AuthUtils.isAuthenticated()) {
      AuthUtils.redirectToLogin();
      return;
    }

    setIsSubmitting(true);

    try {
      // Build payload matching LogBook + AI system structure
      const logbookData = {
        "stack": taskStack,
        "task": tasksCompleted.trim() || (status === 'leave' ? "On Leave" : ""),
        "progress": status === 'leave' ? "On Leave" : (challengesFaced.trim() || "No challenges faced"),
        "blockers": status === 'leave' ? "On Leave" : (plansForTomorrow.trim() || "No specific plans"),
        "status": status
      };

      console.log('Submitting logbook entry:', logbookData);

      const response = await fetch('http://localhost:8000/api/work-updates', {
        method: 'POST',
        headers: AuthUtils.getAuthHeaders(),
        body: JSON.stringify(logbookData)
      });

      if (!response.ok) {
        if (response.status === 401) {
          AuthUtils.redirectToLogin();
          return;
        }
        
        const errorText = await response.text();
        console.error('Raw error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('LogBook submission result:', result);

      if (status === 'leave') {
        // Leave status - saved directly to LogBook
        setShowSuccess(true);
      } else {
        // Working/WFH - needs follow-up to finalize in LogBook
        setTempWorkUpdateId(result.tempWorkUpdateId);
        setShowFollowupRedirect(true);
      }

    } catch (error) {
      console.error('Error submitting to LogBook:', error);
      if (error.message.includes('401') || error.message.includes('Authentication')) {
        AuthUtils.redirectToLogin();
      } else {
        alert('Failed to submit to LogBook: ' + error.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartFollowup = async () => {
    try {
      console.log('Starting follow-up session...');
      
      const response = await fetch(`http://localhost:8000/api/followups/start?temp_work_update_id=${tempWorkUpdateId}`, {
        method: 'POST',
        headers: AuthUtils.getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 401) {
          AuthUtils.redirectToLogin();
          return;
        }
        
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Follow-up session started:', result);

      setFollowupData({
        sessionId: result.sessionId,
        questions: result.questions
      });

      setShowFollowupRedirect(false);
      setShowFollowupQuestions(true);

    } catch (error) {
      console.error('Error starting follow-up:', error);
      throw new Error('Failed to start follow-up session: ' + error.message);
    }
  };

  const handleFollowupSubmit = async (answers) => {
    try {
      console.log('Submitting followup answers:', answers);
      
      const response = await fetch(`http://localhost:8000/api/followup/${followupData.sessionId}/complete`, {
        method: 'PUT',
        headers: AuthUtils.getAuthHeaders(),
        body: JSON.stringify({
          answers: answers
        })
      });

      if (!response.ok) {
        if (response.status === 401) {
          AuthUtils.redirectToLogin();
          return;
        }
        
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Follow-up completed:', result);
      
      setShowFollowupQuestions(false);
      setShowSuccess(true);
      
    } catch (error) {
      console.error('Error submitting followup:', error);
      throw new Error('Failed to submit follow-up answers: ' + error.message);
    }
  };

  const resetForm = () => {
    setTaskStack('');
    setTasksCompleted('');
    setChallengesFaced('');
    setPlansForTomorrow('');
    setStatus('working');
    setTempWorkUpdateId(null);
    setFollowupData(null);
  };

  const handleSuccessClose = () => {
    setShowSuccess(false);
    resetForm();
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f7fa',
      padding: '20px'
    }}>
      {/* Main Form Container */}
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '16px',
        boxShadow: '0 8px 20px rgba(0, 0, 0, 0.08)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
          padding: '32px',
          color: 'white'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px'
            }}>
              📝
            </div>
            <div>
              <h1 style={{
                fontSize: '32px',
                fontWeight: '700',
                margin: '0 0 8px 0'
              }}>
                Daily Activity Log
              </h1>
              <p style={{
                fontSize: '18px',
                margin: 0,
                opacity: 0.9
              }}>
                Complete your daily work summary with AI-powered follow-up
              </p>
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div style={{ padding: '40px' }}>
          {/* Status Selection */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: '600',
              marginBottom: '16px',
              color: '#333',
              fontSize: '18px'
            }}>
              <span style={{ fontSize: '20px' }}>🏢</span>
              Status <span style={{ color: '#e53e3e' }}>*</span>
            </label>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              {[
                { value: 'working', label: 'Working', color: '#2196F3' },
                { value: 'wfh', label: 'Work From Home', color: '#9C27B0' },
                { value: 'leave', label: 'On Leave', color: '#FF9800' }
              ].map(option => (
                <label key={option.value} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'pointer',
                  padding: '16px 20px',
                  border: '2px solid',
                  borderColor: status === option.value ? option.color : '#e0e0e0',
                  borderRadius: '12px',
                  backgroundColor: status === option.value ? `${option.color}15` : 'white',
                  transition: 'all 0.2s ease',
                  fontWeight: status === option.value ? '600' : 'normal',
                  color: status === option.value ? option.color : '#666'
                }}>
                  <input
                    type="radio"
                    value={option.value}
                    checked={status === option.value}
                    onChange={(e) => setStatus(e.target.value)}
                    style={{ 
                      margin: 0,
                      accentColor: option.color
                    }}
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>

          {/* Task Stack */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: '600',
              marginBottom: '12px',
              color: '#333',
              fontSize: '18px'
            }}>
              <span style={{ fontSize: '20px' }}>💻</span>
              Task Stack <span style={{ color: '#e53e3e' }}>*</span>
            </label>
            <select
              value={taskStack}
              onChange={(e) => setTaskStack(e.target.value)}
              style={{
                width: '100%',
                padding: '16px 20px',
                border: '2px solid #e0e0e0',
                borderRadius: '12px',
                fontSize: '16px',
                backgroundColor: 'white',
                color: taskStack ? '#333' : '#999',
                transition: 'border-color 0.2s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = '#2196F3'}
              onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
            >
              <option value="">Select your stack...</option>
              {taskStacks.map(stack => (
                <option key={stack} value={stack}>{stack}</option>
              ))}
            </select>
          </div>

          {/* Tasks Completed - Show for working/wfh */}
          {(status === 'working' || status === 'wfh') && (
            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: '600',
                marginBottom: '12px',
                color: '#333',
                fontSize: '18px'
              }}>
                <span style={{ fontSize: '20px' }}>✅</span>
                Tasks Completed <span style={{ color: '#e53e3e' }}>*</span>
              </label>
              <textarea
                value={tasksCompleted}
                onChange={(e) => setTasksCompleted(e.target.value)}
                placeholder="What did you accomplish today? Be specific about tasks completed, features implemented, bugs fixed, etc..."
                rows={4}
                style={{
                  width: '100%',
                  padding: '16px 20px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '12px',
                  fontSize: '16px',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                  lineHeight: '1.6',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = '#2196F3'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              />
            </div>
          )}

          {/* Challenges Faced - Show for working/wfh */}
          {(status === 'working' || status === 'wfh') && (
            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: '600',
                marginBottom: '12px',
                color: '#333',
                fontSize: '18px'
              }}>
                <span style={{ fontSize: '20px' }}>⚠️</span>
                Challenges Faced
              </label>
              <textarea
                value={challengesFaced}
                onChange={(e) => setChallengesFaced(e.target.value)}
                placeholder="Any obstacles, technical issues, or difficulties you encountered today..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '16px 20px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '12px',
                  fontSize: '16px',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                  lineHeight: '1.6',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = '#FF9800'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              />
            </div>
          )}

          {/* Plans for Tomorrow - Show for working/wfh */}
          {(status === 'working' || status === 'wfh') && (
            <div style={{ marginBottom: '40px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: '600',
                marginBottom: '12px',
                color: '#333',
                fontSize: '18px'
              }}>
                <span style={{ fontSize: '20px' }}>🎯</span>
                Plans for Tomorrow
              </label>
              <textarea
                value={plansForTomorrow}
                onChange={(e) => setPlansForTomorrow(e.target.value)}
                placeholder="What tasks will you focus on tomorrow? Any specific goals or priorities..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '16px 20px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '12px',
                  fontSize: '16px',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                  lineHeight: '1.6',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = '#9C27B0'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              />
            </div>
          )}

          {/* Submit Button */}
          <div style={{ marginBottom: '20px' }}>
            <button
              onClick={handleSubmitLogbook}
              disabled={isSubmitting}
              style={{
                width: '100%',
                padding: '20px 24px',
                backgroundColor: isSubmitting ? '#cccccc' : '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '18px',
                fontWeight: '600',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                transition: 'all 0.2s ease',
                boxShadow: isSubmitting ? 'none' : '0 4px 12px rgba(33, 150, 243, 0.3)'
              }}
            >
              <span style={{ fontSize: '20px' }}>📅</span>
              {isSubmitting ? 'Submitting...' : 'Submit Logbook'}
            </button>
          </div>

          {/* Status indicators */}
          {status === 'leave' && (
            <div style={{
              padding: '16px 20px',
              backgroundColor: '#fff3cd',
              border: '1px solid #ffeaa7',
              borderRadius: '12px',
              color: '#856404',
              fontSize: '14px',
              textAlign: 'center',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}>
              <span>ℹ️</span>
              No additional details or follow-up required for leave days
            </div>
          )}

          {(status === 'working' || status === 'wfh') && (
            <div style={{
              padding: '16px 20px',
              backgroundColor: '#e3f2fd',
              border: '1px solid #bbdefb',
              borderRadius: '12px',
              color: '#1565c0',
              fontSize: '14px',
              textAlign: 'center',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}>
              <span>🤖</span>
              AI follow-up questions will be generated after submission to ensure quality
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px 40px',
          borderTop: '1px solid #e0e0e0',
          fontSize: '14px',
          color: '#666',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0 }}>
            Powered by TalentHub LogBook System with AI Enhancement | 
            Your data is secure and only accessible to authorized supervisors
          </p>
        </div>
      </div>

      {/* Follow-up Redirect Screen */}
      {showFollowupRedirect && (
        <FollowupRedirectScreen
          tempWorkUpdateId={tempWorkUpdateId}
          onStartFollowup={handleStartFollowup}
        />
      )}

      {/* Follow-up Questions Popup */}
      {showFollowupQuestions && followupData && (
        <FollowupQuestionsPopup
          sessionId={followupData.sessionId}
          questions={followupData.questions}
          isOpen={showFollowupQuestions}
          onClose={() => {
            setShowFollowupQuestions(false);
            resetForm();
          }}
          onSubmit={handleFollowupSubmit}
        />
      )}

      {/* Success Screen */}
      {showSuccess && (
        <SuccessScreen onClose={handleSuccessClose} />
      )}
    </div>
  );
};

// Main App Component with Authentication Guard
const App = () => {
  return (
    <AuthGuard>
      <LogBookIntegration />
    </AuthGuard>
  );
};

export default App;