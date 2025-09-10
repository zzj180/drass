import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import {
  Box,
  Typography,
  Link,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import 'katex/dist/katex.min.css';
import 'highlight.js/styles/github-dark.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Styled components for custom rendering
const CodeBlock = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f6f8fa',
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  overflowX: 'auto',
  fontSize: '0.875rem',
  fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
  '& code': {
    backgroundColor: 'transparent',
    padding: 0,
  },
}));

const InlineCode = styled('code')(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#3a3a3a' : '#e9ecef',
  borderRadius: 3,
  padding: '2px 6px',
  fontSize: '0.875em',
  fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
}));

/**
 * Markdown renderer component with support for GFM, math, and syntax highlighting
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className,
}) => {
  return (
    <Box className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
          // Headings
          h1: ({ children }) => (
            <Typography variant="h4" gutterBottom>
              {children}
            </Typography>
          ),
          h2: ({ children }) => (
            <Typography variant="h5" gutterBottom>
              {children}
            </Typography>
          ),
          h3: ({ children }) => (
            <Typography variant="h6" gutterBottom>
              {children}
            </Typography>
          ),
          
          // Paragraphs
          p: ({ children }) => (
            <Typography variant="body1" paragraph>
              {children}
            </Typography>
          ),
          
          // Links
          a: ({ href, children }) => (
            <Link
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              underline="hover"
            >
              {children}
            </Link>
          ),
          
          // Code blocks
          pre: ({ children }) => (
            <CodeBlock>
              {children}
            </CodeBlock>
          ),
          
          // Inline code
          code: ({ inline, children, ...props }) => {
            if (inline) {
              return <InlineCode>{children}</InlineCode>;
            }
            return <code {...props}>{children}</code>;
          },
          
          // Lists
          ul: ({ children }) => (
            <List dense>
              {children}
            </List>
          ),
          ol: ({ children }) => (
            <List dense component="ol" sx={{ listStyleType: 'decimal', pl: 2 }}>
              {children}
            </List>
          ),
          li: ({ children }) => (
            <ListItem sx={{ display: 'list-item', py: 0.5 }}>
              <ListItemText primary={children} />
            </ListItem>
          ),
          
          // Tables
          table: ({ children }) => (
            <TableContainer component={Paper} variant="outlined" sx={{ my: 2 }}>
              <Table size="small">
                {children}
              </Table>
            </TableContainer>
          ),
          thead: ({ children }) => <TableHead>{children}</TableHead>,
          tbody: ({ children }) => <TableBody>{children}</TableBody>,
          tr: ({ children }) => <TableRow>{children}</TableRow>,
          td: ({ children }) => <TableCell>{children}</TableCell>,
          th: ({ children }) => (
            <TableCell component="th" sx={{ fontWeight: 'bold' }}>
              {children}
            </TableCell>
          ),
          
          // Horizontal rule
          hr: () => <Divider sx={{ my: 2 }} />,
          
          // Blockquote
          blockquote: ({ children }) => (
            <Box
              sx={{
                borderLeft: 4,
                borderColor: 'primary.main',
                pl: 2,
                py: 1,
                my: 2,
                bgcolor: 'action.hover',
                borderRadius: 1,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {children}
              </Typography>
            </Box>
          ),
          
          // Strong/Bold
          strong: ({ children }) => (
            <Typography component="span" fontWeight="bold">
              {children}
            </Typography>
          ),
          
          // Emphasis/Italic
          em: ({ children }) => (
            <Typography component="span" fontStyle="italic">
              {children}
            </Typography>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
};

export default MarkdownRenderer;