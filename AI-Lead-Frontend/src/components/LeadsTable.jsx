import React, { useState } from "react";
import {
  Table,
  Mail,
  Phone,
  Star,
  Sparkles,
  Download,
  CheckCircle
} from "lucide-react";


const getScoreTag = (score) => {
  if (score === null || score === undefined) return <span className="text-gray-400">N/A</span>;
  if (score >= 70) return <span className="text-green-600 font-semibold">High</span>;
  if (score >= 40) return <span className="text-yellow-600 font-semibold">Mid</span>;
  return <span className="text-red-600 font-semibold">Low</span>;
};


const LeadsTable = ({ leads }) => {
  const [showToast, setShowToast] = useState(false);

  const exportToCSV = () => {
    if (leads.length === 0) return;

    const headers = [
      "Phone",
      "Email",
      "Credit Score",
      "Age Group",
      "Marital Status",
      "Comments",
      "Consent",
      "Initial Score",
      "Reranked Score",
    ];

    const rows = leads.map((lead) => [
      lead.phone,
      lead.email,
      lead.creditScore,
      lead.ageGroup,
      lead.maritalStatus,
      `"${lead.comments}"`,
      lead.consent ? "Yes" : "No",
      lead.initialScore ?? "N/A",
      lead.rerankedScore ?? "N/A",
    ]);

    const csvContent = [headers, ...rows]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "leads_export.csv";
    link.click();
    URL.revokeObjectURL(url);

    setShowToast(true);
    setTimeout(() => setShowToast(false), 2000);
  };

  return (
    <div className="relative w-full max-w-6xl bg-white p-6 rounded-xl shadow-md animate-fadeIn">
      {showToast && (
        <div className="absolute top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-md flex items-center gap-2 shadow-lg animate-fadeIn">
          <CheckCircle className="w-5 h-5" />
          Leads exported as CSV!
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-gray-800 flex items-center gap-2">
          <Table className="w-6 h-6 text-blue-500" />
          Submitted Leads
        </h2>

        {leads.length > 0 && (
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm transition"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        )}
      </div>

      {leads.length === 0 ? (
        <p className="text-gray-500 text-center">No leads submitted yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 text-sm">
            <thead className="bg-slate-100 text-gray-700 uppercase">
              <tr>
                <th className="px-4 py-2 border"><Phone className="w-4 h-4 inline mr-1 text-blue-500" />Phone</th>
                <th className="px-4 py-2 border"><Mail className="w-4 h-4 inline mr-1 text-purple-500" />Email</th>
                <th className="px-4 py-2 border">Credit Score</th>
                <th className="px-4 py-2 border">Age Group</th>
                <th className="px-4 py-2 border">Marital Status</th>
                <th className="px-4 py-2 border">Comments</th>
                <th className="px-4 py-2 border">Consent</th>
                <th className="px-4 py-2 border"><Star className="w-4 h-4 inline mr-1 text-yellow-500" />Initial</th>
                <th className="px-4 py-2 border"><Sparkles className="w-4 h-4 inline mr-1 text-indigo-600" />Re-ranked</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead, index) => (
                <tr key={index} className="text-center hover:bg-slate-50 transition">
                  <td className="px-4 py-2 border">{lead.phone}</td>
                  <td className="px-4 py-2 border">{lead.email}</td>
                  <td className="px-4 py-2 border">{lead.creditScore}</td>
                  <td className="px-4 py-2 border">{lead.ageGroup}</td>
                  <td className="px-4 py-2 border">{lead.maritalStatus}</td>
                  <td className="px-4 py-2 border">{lead.comments}</td>
                  <td className="px-4 py-2 border">{lead.consent ? "Yes" : "No"}</td>
                  <td className="px-4 py-2 border">{getScoreTag(lead.initialScore)}</td>
                  <td className="px-4 py-2 border">{getScoreTag(lead.rerankedScore)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default LeadsTable;
