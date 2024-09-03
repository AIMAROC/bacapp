import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, Select, MenuItem, FormControl, InputLabel, Card, CardContent, Snackbar, CircularProgress, Tabs, Tab, Paper, Divider, Chip, IconButton, useTheme } from '@mui/material';
import { styled } from '@mui/system';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import remarkMath from 'remark-math';
import 'katex/dist/katex.min.css';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { LightbulbOutlined, School, QuestionAnswer, ContentCopy } from '@mui/icons-material';

const StyledCard = styled(Card)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[3],
  transition: 'box-shadow 0.3s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[6],
  },
}));

const ResponsePaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginTop: theme.spacing(3),
  backgroundColor: theme.palette.grey[50],
  borderLeft: `4px solid ${theme.palette.primary.main}`,
}));

const StyledReactMarkdown = styled(ReactMarkdown)(({ theme }) => ({
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(1),
    color: theme.palette.primary.main,
  },
  '& p': {
    marginBottom: theme.spacing(2),
  },
  '& ul, & ol': {
    paddingLeft: theme.spacing(3),
  },
  '& li': {
    marginBottom: theme.spacing(1),
  },
  '& code': {
    backgroundColor: theme.palette.grey[100],
    padding: theme.spacing(0.5, 1),
    borderRadius: theme.shape.borderRadius,
    fontSize: '0.9em',
  },
  '& pre': {
    margin: theme.spacing(2, 0),
  },
  '& blockquote': {
    borderLeft: `4px solid ${theme.palette.grey[300]}`,
    paddingLeft: theme.spacing(2),
    margin: theme.spacing(2, 0),
    color: theme.palette.text.secondary,
  },
}));
function Dashboard({ setIsAuthenticated }) {
  const theme = useTheme();
  const [subject, setSubject] = useState('');
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [studyTips, setStudyTips] = useState('');
  const [practiceQuestions, setPracticeQuestions] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [topic, setTopic] = useState(''); // New state for topic  
  
  
  useEffect(() => {
    // Fetch user profile or any initial data here
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('http://127.0.0.1:8000/question', 
        { subject, question },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      setResponse(res.data.response);
      setError('');
      setSnackbarMessage('Question answered successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      setError('Failed to get response. Please try again.');
      setSnackbarMessage('Error: Failed to get response');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGetStudyTips = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`http://127.0.0.1:8000/study_tips/${subject}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setStudyTips(res.data.study_tips);
      setSnackbarMessage('Study tips fetched successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      setError('Failed to get study tips. Please try again.');
      setSnackbarMessage('Error: Failed to get study tips');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGetPracticeQuestions = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('http://127.0.0.1:8000/practice', 
        { subject, topic, difficulty },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      setPracticeQuestions(res.data.questions);
      setSnackbarMessage('Practice questions generated successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      setError('Failed to get practice questions. Please try again.');
      setSnackbarMessage('Error: Failed to get practice questions');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbarMessage('Copied to clipboard!');
    setSnackbarOpen(true);
  };

  const renderResponse = (content, title) => (
    <ResponsePaper elevation={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" color="primary">
          {title}
        </Typography>
        <IconButton onClick={() => copyToClipboard(content)} size="small">
          <ContentCopy fontSize="small" />
        </IconButton>
      </Box>
      <Divider />
      <Box mt={2}>
        <StyledReactMarkdown
          rehypePlugins={[rehypeKatex]}
          remarkPlugins={[remarkMath]}
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={atomDark}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {content}
        </StyledReactMarkdown>
      </Box>
    </ResponsePaper>
  );

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom color="primary">
          Tunisian Baccalaureate AI Tutor
        </Typography>
        <Button onClick={handleLogout} variant="outlined" sx={{ mb: 2 }}>
          Logout
        </Button>

        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          sx={{ mb: 2 }}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab icon={<QuestionAnswer />} label="Ask Question" />
          <Tab icon={<LightbulbOutlined />} label="Study Tips" />
          <Tab icon={<School />} label="Practice Questions" />
        </Tabs>

        <StyledCard>
          <CardContent>
            {tabValue === 0 && (
              <form onSubmit={handleSubmit}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="subject-label">Subject</InputLabel>
                  <Select
                    labelId="subject-label"
                    value={subject}
                    label="Subject"
                    onChange={(e) => setSubject(e.target.value)}
                    required
                  >
                    <MenuItem value="mathematics">Mathematics</MenuItem>
                    <MenuItem value="physics">Physics</MenuItem>
                    <MenuItem value="chemistry">Chemistry</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  margin="normal"
                  label="Your Question"
                  multiline
                  rows={4}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  required
                />
                <Button 
                  type="submit" 
                  variant="contained" 
                  sx={{ mt: 2 }} 
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                  {loading ? 'Asking...' : 'Ask Question'}
                </Button>
              </form>
            )}

            {tabValue === 1 && (
              <>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="subject-label">Subject</InputLabel>
                  <Select
                    labelId="subject-label"
                    value={subject}
                    label="Subject"
                    onChange={(e) => setSubject(e.target.value)}
                    required
                  >
                    <MenuItem value="mathematics">Mathematics</MenuItem>
                    <MenuItem value="physics">Physics</MenuItem>
                    <MenuItem value="chemistry">Chemistry</MenuItem>
                  </Select>
                </FormControl>
                <Button 
                  onClick={handleGetStudyTips} 
                  variant="contained" 
                  sx={{ mt: 2 }} 
                  disabled={loading || !subject}
                  startIcon={loading ? <CircularProgress size={20} /> : <LightbulbOutlined />}
                >
                  {loading ? 'Fetching Tips...' : 'Get Study Tips'}
                </Button>
              </>
            )}

            {tabValue === 2 && (
              <>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="subject-label">Subject</InputLabel>
                  <Select
                    labelId="subject-label"
                    value={subject}
                    label="Subject"
                    onChange={(e) => setSubject(e.target.value)}
                    required
                  >
                    <MenuItem value="mathematics">Mathematics</MenuItem>
                    <MenuItem value="physics">Physics</MenuItem>
                    <MenuItem value="chemistry">Chemistry</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  margin="normal"
                  label="Topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  required
                />
                <FormControl fullWidth margin="normal">
                  <InputLabel id="difficulty-label">Difficulty</InputLabel>
                  <Select
                    labelId="difficulty-label"
                    value={difficulty}
                    label="Difficulty"
                    onChange={(e) => setDifficulty(e.target.value)}
                    required
                  >
                    <MenuItem value="easy">Easy</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="hard">Hard</MenuItem>
                  </Select>
                </FormControl>
                <Button 
                  onClick={handleGetPracticeQuestions} 
                  variant="contained" 
                  sx={{ mt: 2 }} 
                  disabled={loading || !subject || !topic}
                  startIcon={loading ? <CircularProgress size={20} /> : <School />}
                >
                  {loading ? 'Generating Questions...' : 'Get Practice Questions'}
                </Button>
              </>
            )}
          </CardContent>
        </StyledCard>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}

        {response && tabValue === 0 && renderResponse(response, "AI Tutor's Response")}
        {studyTips && tabValue === 1 && renderResponse(studyTips, "Study Tips")}
        {practiceQuestions && tabValue === 2 && renderResponse(practiceQuestions, "Practice Questions")}

        <Snackbar
          open={snackbarOpen}
          autoHideDuration={6000}
          onClose={() => setSnackbarOpen(false)}
          message={snackbarMessage}
        />
      </Box>
    </Container>
  );
}

export default Dashboard;