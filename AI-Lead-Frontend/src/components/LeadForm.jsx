// ...imports remain unchanged
import axios from "axios";
import React, { useState } from "react";
import {
  Mail,
  Phone,
  Check,
  CreditCard,
  MessageCircle,
  User
} from "lucide-react";



const LeadForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    phone: "",
    email: "",
    creditScore: "",
    ageGroup: "",
    maritalStatus: "",
    comments: "",
    consent: false,
    annualIncome: "",
    netWorth: "",
    employmentStatus: "",
  });

  const [showToast, setShowToast] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.consent) {
      alert("❗ Please consent to data processing.");
      return;
    }

    try {
      const response = await axios.post("http://localhost:8000/score", formData);
      const { initialScore, rerankedScore } = response.data;

      const newLead = {
        ...formData,
        initialScore,
        rerankedScore,
      };
      

      console.log("✅ Lead submitted to backend:", newLead);
      onSubmit(newLead);

      setShowToast(true);
      setTimeout(() => setShowToast(false), 2000);

      // Reset
      setFormData({
        phone: "",
        email: "",
        creditScore: "",
        ageGroup: "",
        maritalStatus: "",
        comments: "",
        consent: false,
        annualIncome: "",
        netWorth: "",
        employmentStatus: "",
      });
    } catch (error) {
      console.error("❌ Error submitting lead:", error);
      alert("Something went wrong while submitting. Please check your FastAPI backend.");
    }
  };

  return (
    <div className="w-full max-w-3xl bg-white p-8 rounded-xl shadow-xl mb-10 relative animate-fadeIn">
      {showToast && (
        <div className="absolute top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-md flex items-center gap-2 shadow-lg animate-fadeIn">
          <Check className="w-5 h-5" />
          Lead Submitted!
        </div>
      )}

      <h2 className="text-2xl font-bold text-indigo-700 mb-6 flex items-center gap-2">
        <User className="w-6 h-6" />
        Add Lead
      </h2>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Phone */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <Phone className="w-4 h-4" /> Phone Number
          </label>
          <input
            type="text"
            required
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="+91-9876543210"
          />
        </div>

        {/* Email */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <Mail className="w-4 h-4" /> Email
          </label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="john@example.com"
          />
        </div>

        {/* Credit Score */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <CreditCard className="w-4 h-4" /> Credit Score
          </label>
          <input
            type="number"
            required
            min="300"
            max="850"
            value={formData.creditScore}
            onChange={(e) => setFormData({ ...formData, creditScore: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="700"
          />
        </div>

        {/* Age Group */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1">Age Group</label>
          <select
            value={formData.ageGroup}
            onChange={(e) => setFormData({ ...formData, ageGroup: e.target.value })}
            className="border rounded px-3 py-2"
            required
          >
            <option value="">Select...</option>
            <option value="18-25">18-25</option>
            <option value="26-35">26-35</option>
            <option value="36-50">36-50</option>
            <option value="51+">51+</option>

          </select>
        </div>

        {/* Marital Status */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1">Marital Status</label>
          <select
            value={formData.maritalStatus}
            onChange={(e) => setFormData({ ...formData, maritalStatus: e.target.value })}
            className="border rounded px-3 py-2"
            required
          >
            <option value="">Select...</option>
            <option value="Single">Single</option>
            <option value="Married">Married</option>
            <option value="Married with Kids">Married with Kids</option>
          </select>
        </div>

        {/* Annual Income */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1">Annual Income (INR)</label>
          <input
            type="number"
            value={formData.annualIncome}
            onChange={(e) => setFormData({ ...formData, annualIncome: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="800000"
            required
          />
        </div>

        {/* Net Worth */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1">Net Worth (INR)</label>
          <input
            type="number"
            value={formData.netWorth}
            onChange={(e) => setFormData({ ...formData, netWorth: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="2000000"
            required
          />
        </div>

        {/* Employment Status */}
        <div className="flex flex-col">
          <label className="text-sm text-gray-600 mb-1">Employment Status</label>
          <select
            value={formData.employmentStatus}
            onChange={(e) => setFormData({ ...formData, employmentStatus: e.target.value })}
            className="border rounded px-3 py-2"
            required
          >
            <option value="">Select...</option>
            <option value="Employed">Employed</option>
            <option value="Unemployed">Unemployed</option>
            <option value="Student">Student</option>
            <option value="Self-employed">Self-employed</option>
          </select>
        </div>

        {/* Comments */}
        <div className="flex flex-col md:col-span-2">
          <label className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <MessageCircle className="w-4 h-4" /> Comments
          </label>
          <textarea
            rows="3"
            value={formData.comments}
            onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
            className="border rounded px-3 py-2"
            placeholder="Optional feedback..."
          />
        </div>

        {/* Consent */}
        <div className="flex items-center md:col-span-2 mt-2">
          <input
            type="checkbox"
            checked={formData.consent}
            onChange={(e) => setFormData({ ...formData, consent: e.target.checked })}
            className="mr-2"
            required
          />
          <label className="text-sm text-gray-600">
            I consent to data processing.
          </label>
        </div>

        {/* Submit */}
        <div className="md:col-span-2 flex justify-end mt-4">
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md"
          >
            Submit Lead
          </button>
        </div>
      </form>
    </div>
  );
};

export default LeadForm;
