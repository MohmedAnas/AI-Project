import { useState } from 'react';
import LeadForm from './components/LeadForm';
import LeadsTable from './components/LeadsTable';

function App() {
  const [leads, setLeads] = useState([]);

  const handleLeadSubmit = (leadData) => {
    console.log("✅ App.jsx received new lead:", leadData);
    setLeads((prev) => [...prev, leadData]);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <LeadForm onSubmit={handleLeadSubmit} />
      <LeadsTable leads={leads} />
    </div>
  );
}

export default App;
