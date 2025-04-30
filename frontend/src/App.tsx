import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Paper,
  Tab,
  Tabs,
} from '@mui/material';
import { api, Framework, GenerateCodeResponse } from './services/api';
import CodeDisplay from './components/CodeDisplay';
import ConfigViewer from './components/ConfigViewer';
import WorkflowSlideInfo from './components/WorkflowSlideInfo';
import { WorkflowMode, WorkflowPattern, WORKFLOW_PATTERNS } from './types/workflows';

function App() {
  const [mode, setMode] = useState<WorkflowMode['type']>('framework');
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<string>('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateCodeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);

  useEffect(() => {
    loadFrameworks();
  }, []);

  const loadFrameworks = async () => {
    try {
      const data = await api.getFrameworks();
      setFrameworks(data);
    } catch (err) {
      setError('Failed to load frameworks');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'framework' && !selectedFramework) {
      setError('Please select a framework');
      return;
    }

    if (mode === 'workflow_pattern' && !selectedWorkflow) {
      setError('Please select a workflow pattern');
      return;
    }

    if (!prompt) {
      setError('Please describe your requirements');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.generateCode({
        prompt,
        framework: mode === 'framework' ? selectedFramework : selectedWorkflow,
      });
      setResult(response);
      setActiveTab(0); // Switch to configuration view
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          🤖 AdaptFlow
        </Typography>
        
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Tabs
            value={mode}
            onChange={(_, newValue) => {
              setMode(newValue);
              setSelectedFramework('');
              setSelectedWorkflow('');
              setPrompt('');
            }}
            sx={{ mb: 3 }}
          >
            <Tab value="framework" label="Framework" />
            <Tab value="workflow_pattern" label="Workflow Pattern" />
          </Tabs>

          <form onSubmit={handleSubmit}>
            {mode === 'framework' ? (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Framework</InputLabel>
                <Select
                  value={selectedFramework}
                  label="Framework"
                  onChange={(e) => setSelectedFramework(e.target.value)}
                >
                  {frameworks.map((framework) => (
                    <MenuItem key={framework.id} value={framework.id}>
                      {framework.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <Box sx={{ mb: 4 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Workflow Pattern</InputLabel>
                  <Select
                    value={selectedWorkflow}
                    label="Workflow Pattern"
                    onChange={(e) => {
                      setSelectedWorkflow(e.target.value);
                      const pattern = WORKFLOW_PATTERNS.find((p: WorkflowPattern) => p.id === e.target.value);
                      if (pattern) {
                        setPrompt('');
                      }
                    }}
                  >
                    {WORKFLOW_PATTERNS.map((pattern) => (
                      <MenuItem key={pattern.id} value={pattern.id}>
                        <Box>
                          <Typography>{pattern.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {pattern.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                {selectedWorkflow && (
                  <WorkflowSlideInfo 
                    selectedWorkflow={WORKFLOW_PATTERNS.find(p => p.id === selectedWorkflow) || null} 
                  />
                )}
              </Box>
            )}

            <TextField
              fullWidth
              multiline
              rows={4}
              label={mode === 'framework' ? 
                "Describe your requirements" : 
                "Describe your workflow requirements"
              }
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              sx={{ mb: 2 }}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{ height: 48 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Code'}
            </Button>
          </form>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs
                value={activeTab}
                onChange={(_, newValue) => setActiveTab(newValue)}
              >
                <Tab label="Configuration" />
                <Tab label="Generated Code" />
              </Tabs>
            </Box>

            {activeTab === 0 && (
              <ConfigViewer 
                config={result.config} 
                framework={mode === 'framework' ? selectedFramework : selectedWorkflow} 
              />
            )}
            {activeTab === 1 && <CodeDisplay code={result.code} />}
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App;
