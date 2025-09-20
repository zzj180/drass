import React, { useState } from 'react';
import { Box, Button, Typography, Dialog, DialogTitle, DialogContent } from '@mui/material';

const TestKnowledgePage: React.FC = () => {
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleButtonClick = () => {
    console.log('Button clicked!');
    alert('Button clicked!');
    setDialogOpen(true);
  };

  return (
    <Box p={3}>
      <Typography variant="h4">Test Knowledge Page</Typography>
      
      <Button 
        variant="contained" 
        onClick={handleButtonClick}
        sx={{ mt: 2 }}
      >
        Test Upload Button
      </Button>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Test Dialog</DialogTitle>
        <DialogContent>
          <Typography>Dialog is working!</Typography>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default TestKnowledgePage;
