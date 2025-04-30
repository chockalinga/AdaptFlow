import React, { useEffect, useState } from 'react';
import { WorkflowPattern } from '../types/workflows';
import './WorkflowSlideInfo.css';

interface WorkflowSlideInfoProps {
  selectedWorkflow: WorkflowPattern | null;
}

const WorkflowSlideInfo: React.FC<WorkflowSlideInfoProps> = ({ selectedWorkflow }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [contentVisible, setContentVisible] = useState(false);

  useEffect(() => {
    if (selectedWorkflow) {
      setIsVisible(true);
      // Delay content fade in for smooth transition
      setTimeout(() => setContentVisible(true), 300);
    } else {
      setContentVisible(false);
      setTimeout(() => setIsVisible(false), 300);
    }
  }, [selectedWorkflow]);

  if (!selectedWorkflow) return null;

  return (
    <div className={`workflow-slide-container ${isVisible ? 'active' : ''}`}>
      <div className={`workflow-content ${contentVisible ? 'active' : ''}`}>
        <h2>{selectedWorkflow.name}</h2>
        <p className="description">{selectedWorkflow.description}</p>
        
        {selectedWorkflow.detailedDescription && (
          <div className="detailed-description">
            <h3>How it works</h3>
            <p>{selectedWorkflow.detailedDescription}</p>
          </div>
        )}

        {selectedWorkflow.examples && selectedWorkflow.examples.length > 0 && (
          <div className="examples">
            <h3>Examples</h3>
            {selectedWorkflow.examples.map((example, index) => (
              <div key={index} className="example-card">
                <h4>{example.scenario}</h4>
                <p>{example.implementation}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowSlideInfo;
