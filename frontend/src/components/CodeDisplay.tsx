import React from 'react';
import { Paper, IconButton, Tooltip } from '@mui/material';
import { ContentCopy } from '@mui/icons-material';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('python', python);

interface CodeDisplayProps {
  code: string;
}

const CodeDisplay: React.FC<CodeDisplayProps> = ({ code }) => {
  const handleCopyClick = () => {
    navigator.clipboard.writeText(code);
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        position: 'relative',
        marginTop: 2,
        marginBottom: 2,
        '& pre': {
          margin: 0,
          padding: '16px !important',
          maxHeight: '500px',
          overflow: 'auto'
        }
      }}
    >
      <Tooltip title="Copy code">
        <IconButton
          onClick={handleCopyClick}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
            },
          }}
        >
          <ContentCopy />
        </IconButton>
      </Tooltip>
      <SyntaxHighlighter
        language="python"
        style={docco}
        customStyle={{
          fontSize: '14px',
          lineHeight: '1.5',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </Paper>
  );
};

export default CodeDisplay;
