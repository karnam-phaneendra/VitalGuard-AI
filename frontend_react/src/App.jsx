import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Activity, 
  Users, 
  Upload, 
  PlusCircle, 
  LogOut, 
  ShieldAlert, 
  CreditCard, 
  Stethoscope,
  CheckCircle2,
  XCircle,
  X,
  AlertTriangle,
  History,
  Thermometer,
  Calendar,
  ChevronRight,
  Trash2
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { motion, AnimatePresence } from 'framer-motion';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [view, setView] = useState('login');
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [criticalAlert, setCriticalAlert] = useState(null);
  
  // Login State
  const [loginMode, setLoginMode] = useState('patient'); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [patientIdInput, setPatientIdInput] = useState('');

  // Axios Security Header
  useEffect(() => {
    if (user?.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${user.token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [user]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (loginMode === 'admin') {
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);
        const res = await axios.post(`${API_BASE}/login`, formData);
        setUser(res.data);
        setView('admin');
      } else {
        // Patient Login: Verify ID and set session
        try {
          const res = await axios.get(`${API_BASE}/patient/${patientIdInput}`);
          setUser({ role: 'patient', patient_id: patientIdInput, ...res.data });
          setView('patient');
        } catch {
          setError("Invalid Patient ID");
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }
  };

  const logout = () => {
    setUser(null);
    setView('login');
    setEmail('');
    setPassword('');
    setPatientIdInput('');
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white">
      <AnimatePresence>
        {criticalAlert && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -20 }}
            className="fixed top-24 left-1/2 -translate-x-1/2 z-[100] w-full max-w-md px-4"
          >
            <div className="bg-red-500 rounded-2xl p-4 shadow-2xl flex items-center gap-4 border border-red-400">
              <div className="bg-white/20 p-2 rounded-xl">
                <AlertTriangle className="text-white w-6 h-6" />
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-white uppercase text-xs tracking-widest">⚠ CRITICAL VITAL ALERT</h4>
                <p className="text-white font-medium">{criticalAlert}</p>
              </div>
              <button onClick={() => setCriticalAlert(null)} className="p-1 hover:bg-white/10 rounded-lg">
                <XCircle className="w-5 h-5 text-white" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {view === 'login' && (
        <div className="min-h-screen flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-md w-full bg-[#1e293b] rounded-3xl p-8 shadow-2xl border border-white/5"
          >
            <div className="flex justify-center mb-8">
              <div className="p-4 bg-indigo-500/10 rounded-2xl">
                <Activity className="w-12 h-12 text-indigo-500" />
              </div>
            </div>
            <h1 className="text-3xl font-bold text-center mb-2 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent italic">
              VitalGuard AI
            </h1>
            <p className="text-gray-400 text-center mb-8">Smart Hospital Management System</p>

            <div className="flex bg-[#0f172a] p-1 rounded-xl mb-8">
              {['patient', 'admin'].map(mode => (
                <button 
                  key={mode}
                  onClick={() => {setLoginMode(mode); setError('')}}
                  className={`flex-1 py-2 rounded-lg font-medium capitalize transition-all ${loginMode === mode ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400'}`}
                >
                  {mode}
                </button>
              ))}
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              {loginMode === 'admin' ? (
                <>
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase mb-2">Admin Email</label>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full bg-[#0f172a] border border-white/10 rounded-xl px-4 py-3" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase mb-2">Password</label>
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full bg-[#0f172a] border border-white/10 rounded-xl px-4 py-3" />
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase mb-2">Patient ID</label>
                  <input type="text" value={patientIdInput} onChange={(e) => setPatientIdInput(e.target.value)} required className="w-full bg-[#0f172a] border border-white/10 rounded-xl px-4 py-3" />
                </div>
              )}

              {error && <div className="p-3 bg-red-500/10 text-red-400 text-sm rounded-lg flex items-center gap-2"><AlertTriangle size={16}/> {error}</div>}

              <button className="w-full bg-indigo-600 hover:bg-indigo-500 py-4 rounded-xl font-bold shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2">
                Access System <ChevronRight size={20}/>
              </button>
            </form>
          </motion.div>
        </div>
      )}

      {view === 'admin' && <AdminPanel logout={logout} onSelectPatient={(pid) => { setPatientIdInput(pid); setView('patient_detail'); }} setAlert={setCriticalAlert} />}
      {view === 'patient_detail' && <PatientDashboard patient_id={patientIdInput} role={user.role} logout={() => setView('admin')} setAlert={setCriticalAlert} onDischarge={() => setView('discharge_page')} />}
      {view === 'patient' && <PatientDashboard patient_id={user.patient_id} role={user.role} logout={logout} setAlert={setCriticalAlert} onDischarge={() => setView('discharge_page')} />}
      {view === 'discharge_page' && <DischargePage patient_id={user?.role === 'patient' ? user.patient_id : patientIdInput} role={user.role} goBack={() => setView(user?.role === 'patient' ? 'patient' : 'patient_detail')} />}
    </div>
  );
}

function AdminPanel({ logout, onSelectPatient, setAlert }) {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('registry'); // 'registry', 'scan', 'pharmacy'
  const [allAlerts, setAllAlerts] = useState([]);
  const [targetId, setTargetId] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);

  const fetchPatients = async () => {
    try {
      const res = await axios.get(`${API_BASE}/patients`);
      setPatients(res.data);
    } catch (err) { console.error(err); }
    setLoading(false);
  };
    const fetchAllAlerts = async () => {
    try {
      if (patients.length === 0) {
        setAllAlerts([]);
        return;
      }

      const alertResponses = await Promise.all(
        patients.map(p =>
          axios.get(`${API_BASE}/alerts/${p.patient_id}`)
        )
      );

      const combinedAlerts = alertResponses.flatMap((res, index) =>
        res.data.map(alert => ({
        ...alert,
        patient_id: patients[index].patient_id,
        patient_name: patients[index].name || patients[index].full_name
    }))
);

      combinedAlerts.sort(
        (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
      );

      setAllAlerts(combinedAlerts);
    } catch (err) {
      console.error("Error fetching hospital alerts:", err);
    }
  };

  useEffect(() => { fetchPatients(); }, []);
    useEffect(() => {
    fetchAllAlerts();

    const interval = setInterval(fetchAllAlerts, 10000);

    return () => clearInterval(interval);
  }, [patients]);

  const registerPatient = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const res = await axios.post(`${API_BASE}/register_patient`, formData);
    alert(`Registered: ${res.data.patient_id}`);
    fetchPatients();
  };

  const uploadVitals = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      const res = await axios.post(`${API_BASE}/upload_vitals`, formData);
      if (res.data.critical_alerts?.length > 0) setAlert(res.data.critical_alerts[0]);
      alert(`Vitals Processed. Risk: ${res.data.risk_level}`);
    } catch (err) { alert("Error uploading vitals"); }
  };

  return (
    <div className="min-h-screen">
      <nav className="h-20 border-b border-white/5 bg-[#1e293b]/50 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="text-indigo-500" />
          <span className="font-bold text-xl tracking-tight">Admin Console</span>
        </div>
        <div className="flex bg-[#0f172a] p-1 rounded-xl">
          {['registry', 'scan', 'pharmacy'].map(v => (
            <button key={v} onClick={() => setView(v)} className={`px-4 py-2 rounded-lg text-sm font-bold capitalize ${view === v ? 'bg-indigo-600' : 'text-gray-400'}`}>{v}</button>
          ))}
        </div>
        <button onClick={logout} className="text-gray-400 hover:text-white transition-colors"><LogOut/></button>
      </nav>

      <main className="max-w-7xl mx-auto p-6 md:p-10">
        {view === 'registry' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1 bg-[#1e293b] rounded-3xl p-8 border border-white/5 h-fit sticky top-28">
              <h2 className="text-xl font-bold flex items-center gap-3 mb-6"><PlusCircle className="text-indigo-400"/> New Registration</h2>
              <form onSubmit={registerPatient} className="space-y-4">
                <input name="name" placeholder="Full Name" required className="w-full bg-[#0f172a] border border-white/10 p-3 rounded-xl" />
                <div className="grid grid-cols-2 gap-4">
                  <input name="age" type="number" placeholder="Age" required className="w-full bg-[#0f172a] border border-white/10 p-3 rounded-xl" />
                  <input name="doctor" placeholder="Doctor" required className="w-full bg-[#0f172a] border border-white/10 p-3 rounded-xl" />
                </div>
                <input name="disease" placeholder="Primary Diagnosis" required className="w-full bg-[#0f172a] border border-white/10 p-3 rounded-xl" />
                <input name="bed_number" placeholder="Bed / Ward" required className="w-full bg-[#0f172a] border border-white/10 p-3 rounded-xl" />
                <button className="w-full bg-indigo-600 py-4 rounded-xl font-bold">Register Patient</button>
              </form>
            </div>
            <div className="lg:col-span-2 space-y-6">
              <h2 className="text-xl font-bold flex items-center gap-3"><Users className="text-purple-400"/> Registered Patients</h2>
              {/* Hospital-Wide Risk Alerts */}
<section className="bg-[#1e293b] rounded-3xl p-6 border border-rose-500/20 shadow-xl">
  <h3 className="text-sm font-bold text-rose-400 uppercase tracking-widest mb-5 flex items-center gap-2">
    <ShieldAlert size={16} />
    Hospital-Wide Risk Alerts
    <span className="ml-auto bg-rose-500/10 text-rose-400 px-3 py-1 rounded-lg">
      {allAlerts.length}
    </span>
  </h3>

  <div className="space-y-3 max-h-[350px] overflow-y-auto">
    {allAlerts.length > 0 ? (
      allAlerts.slice(0, 10).map((a, i) => (
        <div
          key={a._id || i}
          className="p-4 bg-rose-500/5 rounded-2xl border border-rose-500/10"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="text-rose-500 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-bold text-rose-200">
                {a.message || "Risk alert"}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Patient: {a.patient_name || "Unknown"} ({a.patient_id})
              </p>
              <p className="text-[10px] text-gray-500 mt-1">
                {a.timestamp
                  ? new Date(a.timestamp).toLocaleString()
                  : "Time unavailable"}
              </p>
            </div>
          </div>
        </div>
      ))
    ) : (
      <p className="text-sm text-gray-500 text-center py-5">
        No risk alerts available.
      </p>
    )}
  </div>
</section>
              {loading ? <div className="text-gray-500 italic">Fetching patients...</div> : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {patients.map(p => (
                    <motion.div whileHover={{ scale: 1.02 }} key={p.patient_id} onClick={() => onSelectPatient(p.patient_id)} className="bg-[#1e293b] p-6 rounded-3xl border border-white/5 cursor-pointer hover:border-indigo-500/50 transition-all group">
                      <div className="flex justify-between items-start mb-4">
                        <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                          <Activity size={24}/>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-1 text-[10px] font-black uppercase tracking-wider rounded-lg border ${
                            (p.discharge || p.status === 'discharged')
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
                          }`}>
                            {(p.discharge || p.status === 'discharged') ? '● Discharged' : '● Active'}
                          </span>
                          <span className="text-[10px] font-bold text-gray-400 px-2 py-1 bg-white/5 rounded-md uppercase tracking-widest border border-white/5">{p.patient_id}</span>
                        </div>
                      </div>
                      <h3 className="text-lg font-bold group-hover:text-indigo-400 transition-colors">{p.name || p.full_name}</h3>
                      <p className="text-sm text-gray-400 mb-4">{p.disease || p.primary_diagnosis || "General Checkup"}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Calendar size={12}/> {new Date(p.admission_date?.$date || p.admission_date || Date.now()).toLocaleDateString()}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

       
{view === 'scan' && (
  <div className="max-w-2xl mx-auto bg-[#1e293b] p-8 rounded-3xl border border-white/5">
    <h2 className="text-2xl font-bold flex items-center gap-3 mb-8">
      <Upload className="text-indigo-400" /> Vital Scan (OCR)
    </h2>

    <form onSubmit={uploadVitals} className="space-y-6">
      <input
        type="text"
        name="patient_id"
        placeholder="Patient ID"
        required
        className="w-full bg-[#0f172a] border border-white/10 p-4 rounded-xl"
      />

     
      <div className="relative border-2 border-dashed border-white/10 rounded-2xl p-8 text-center hover:border-indigo-500/50 cursor-pointer group transition-all">
        <input
          type="file"
          name="image"
          accept="image/*"
          required
          onChange={(e) => setSelectedImage(e.target.files[0] || null)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        {selectedImage ? (
          <div className="space-y-3">
            <Activity size={40} className="mx-auto text-green-400" />
            <p className="text-green-400 font-semibold">
              Image selected successfully!
            </p>
            <p className="text-gray-300 text-sm break-all">
              {selectedImage.name}
            </p>
            <p className="text-gray-500 text-xs">
              {(selectedImage.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <>
            <Activity
              size={48}
              className="mx-auto text-gray-600 mb-4 group-hover:text-indigo-400"
            />
            <p className="text-gray-400">Upload monitor snapshot</p>
            <p className="text-gray-500 text-xs mt-2">
              Click to select an image
            </p>
          </>
        )}
      </div>


      <button
        type="submit"
        className="w-full bg-indigo-600 py-4 rounded-xl font-bold text-lg"
      >
        Analyze Vitals
      </button>
    </form>
  </div>
)}


        {view === 'pharmacy' && (
          <div className="max-w-2xl mx-auto bg-[#1e293b] p-8 rounded-3xl border border-white/5">
            <h2 className="text-2xl font-bold flex items-center gap-3 mb-8"><Stethoscope className="text-green-400"/> Prescription Manager</h2>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              try {
                const res = await axios.post(`${API_BASE}/assign_medicine`, formData);
                if (res.data.status === "success") {
                  let msg = `Prescription Assigned!\nMedicine: ${res.data.medicine_name}\nUnit Price: ₹${res.data.unit_price}\nTotal: ₹${res.data.total_cost}\nStock Remaining: ${res.data.stock_remaining} units`;
                  if (res.data.warning_level === "red") {
                    msg += `\n\n🚨 CRITICAL ALERT: Stock is below 50 units!`;
                  } else if (res.data.warning_level === "yellow") {
                    msg += `\n\n⚠️ LOW STOCK WARNING: Stock is 100 units or lower!`;
                  }
                  alert(msg);
                  e.target.reset();
                } else {
                  alert(res.data.message || "Could not assign medicine");
                }
              } catch (err) {
                alert("Error: " + (err.response?.data?.detail || err.message));
              }
            }} className="space-y-6">
              <input name="patient_id" placeholder="Patient ID (e.g., phani)" required className="w-full bg-[#0f172a] border border-white/10 p-4 rounded-xl text-white outline-none focus:border-indigo-500" />
              <input name="medicine_name" placeholder="Medicine Name or Nickname (e.g., cetirizine, dolo, pan)" required className="w-full bg-[#0f172a] border border-white/10 p-4 rounded-xl text-white outline-none focus:border-indigo-500" />
              <input name="quantity" type="number" min="1" placeholder="Quantity" required className="w-full bg-[#0f172a] border border-white/10 p-4 rounded-xl text-white outline-none focus:border-indigo-500" />
              <button className="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-xl font-bold text-lg text-white transition-all">Assign Prescription</button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

function PatientDashboard({ patient_id, role, logout, setAlert, onDischarge }) {
  const [patient, setPatient] = useState(null);
  const [vitals, setVitals] = useState([]);
  const [latestVitals, setLatestVitals] = useState(null);
  const [prescriptions, setPrescriptions] = useState([]);
  const [billing, setBilling] = useState(null);
  const [payments, setPayments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [showPayForm, setShowPayForm] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [prescribing, setPrescribing] = useState(false);
  
  // Pharmacy autocomplete and live stock state
  const [medQuery, setMedQuery] = useState("");
  const [medSuggestions, setMedSuggestions] = useState([]);
  const [selectedMed, setSelectedMed] = useState(null);

  const isAdmin = role === 'admin';

  const fetchData = async () => {
    const safeFetch = async (url, setter) => {
      try {
        const res = await axios.get(url);
        console.log(`FETCHED ${url}:`, res.data);
        setter(res.data);
      } catch (err) { console.error(`Fetch error ${url}:`, err); }
    };

    try {
      safeFetch(`${API_BASE}/patient/${patient_id}`, setPatient);
      safeFetch(`${API_BASE}/vitals/${patient_id}`, setVitals);
      safeFetch(`${API_BASE}/latest_vitals/${patient_id}`, setLatestVitals);
      safeFetch(`${API_BASE}/prescriptions/${patient_id}`, setPrescriptions);
      safeFetch(`${API_BASE}/billing/${patient_id}`, setBilling);
      safeFetch(`${API_BASE}/payments/${patient_id}`, setPayments);
      safeFetch(`${API_BASE}/alerts/${patient_id}`, setAlerts);
    } catch (err) { console.error("Parallel fetch failed", err); }
  };

  useEffect(() => {
    fetchData();
    const inv = setInterval(fetchData, 10000);
    return () => clearInterval(inv);
  }, [patient_id]);

  // Live pharmacy search
  useEffect(() => {
    if (!medQuery || medQuery.trim().length < 2) {
      setMedSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await axios.get(`${API_BASE}/pharmacy/search?q=${encodeURIComponent(medQuery.trim())}&limit=5`);
        setMedSuggestions(res.data || []);
      } catch (e) {
        setMedSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [medQuery]);

  const handleUploadVitals = async (e) => {
    e.preventDefault();
    setUploading(true);
    const formData = new FormData(e.target);
    formData.append('patient_id', patient_id);
    try {
      const res = await axios.post(`${API_BASE}/upload_vitals`, formData);
      if (res.data.critical_alerts?.length > 0) {
        setAlert(res.data.critical_alerts[0]);
      }
      fetchData();
    } catch (err) { alert("Upload failed: " + (err.response?.data?.detail || err.message)); }
    finally { setUploading(false); }
  };

  const handleAssignMedicine = async (e) => {
    e.preventDefault();
    setPrescribing(true);
    const formData = new FormData(e.target);
    formData.append('patient_id', patient_id);
    try {
      const res = await axios.post(`${API_BASE}/assign_medicine`, formData);
      if (res.data.status === "unavailable") {
        alert(res.data.message);
      } else {
        if (res.data.warning_level === "red") {
          alert(`🚨 CRITICAL PHARMACY STOCK ALERT!\n${res.data.warning_message}`);
        } else if (res.data.warning_level === "yellow") {
          alert(`⚠️ LOW PHARMACY STOCK WARNING!\n${res.data.warning_message}`);
        }
      }
      fetchData();
      e.target.reset();
      setMedQuery("");
      setMedSuggestions([]);
      setSelectedMed(null);
    } catch (err) { alert("Prescription failed: " + (err.response?.data?.detail || err.message)); }
    finally { setPrescribing(false); }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    formData.append('patient_id', patient_id);
    try {
      await axios.post(`${API_BASE}/add_payment`, formData);
      setShowPayForm(false);
      fetchData();
    } catch (err) { alert("Payment failed"); }
  };

  const handleDeleteMedicine = async (prescId) => {
    if (!window.confirm("Remove this medicine record?")) return;
    try {
      console.log(`DELETING: ${API_BASE}/prescription/${prescId}`);
      const res = await axios.delete(`${API_BASE}/prescription/${prescId}`);
      console.log("DELETE SUCCESS:", res.data);
      fetchData();
    } catch (err) { 
      console.error("Delete failed:", err.response?.data || err.message);
      alert(`Delete failed: ${err.response?.data?.detail || err.message}`); 
    }
  };

  const handleUpdateCost = async (field, label) => {
    let currentValue = 0;
    if (field === 'bed_cost_per_day') currentValue = billing?.bed_rate || 500;
    else if (field === 'treatment_cost') currentValue = billing?.treatment_cost || 1000;
    else if (field === 'insurance_coverage') currentValue = billing?.insurance_coverage || 0;

    const newValue = window.prompt(`Enter amount for ${label} (₹):`, currentValue);
    if (newValue === null || newValue === "" || isNaN(newValue)) return;
    
    try {
      await axios.post(`${API_BASE}/update_billing_costs`, {
        patient_id,
        field,
        new_value: parseFloat(newValue)
      });
      fetchData();
    } catch (err) { alert("Update failed: " + (err.response?.data?.detail || err.message)); }
  };

  const chartData = {
    labels: vitals.slice(0, 15).map(v => new Date(v.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})).reverse(),
    datasets: [
      {
        label: 'Heart Rate',
        data: vitals.slice(0, 15).map(v => v.heart_rate).reverse(),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true, tension: 0.4,
      },
      {
        label: 'SpO2',
        data: vitals.slice(0, 15).map(v => v.spo2).reverse(),
        borderColor: '#22d3ee',
        fill: false, tension: 0.4,
      },
      {
        label: 'Temp',
        data: vitals.slice(0, 15).map(v => v.temperature).reverse(),
        borderColor: '#fb7185',
        fill: false, tension: 0.4,
      }
    ]
  };

  if (!patient) return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
      <div className="text-center">
        <Activity className="animate-spin text-indigo-500 mb-4 mx-auto" size={48} />
        <p className="text-gray-400 italic">Syncing Health Data...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0f172a] text-white">
      {/* Navigation */}
      <nav className="h-20 border-b border-white/5 bg-[#1e293b]/50 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="text-indigo-500" />
          <span className="font-bold text-xl tracking-tight hidden md:block">{isAdmin ? 'Clinical Management' : 'Patient Monitoring Portal'}</span>
          <span className="font-bold text-xl tracking-tight md:hidden">{isAdmin ? 'Clinical' : 'Portal'}</span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${isAdmin ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'bg-white/5 text-gray-500 border-white/5'}`}>
            {isAdmin ? 'ADMIN CONTROL' : 'READ ONLY'}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <h4 className="text-xs font-bold text-white leading-none">{patient.name}</h4>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{patient.patient_id}</span>
          </div>
          {isAdmin && (
             <button
               onClick={async () => {
                 if (!patient.discharge) {
                   try { await axios.get(`${API_BASE}/decision/${patient_id}`); } catch (e) {}
                 }
                 if (onDischarge) onDischarge();
               }}
               disabled={patient.discharge}
               className={`hidden md:block px-4 py-2 rounded-xl font-bold uppercase text-[10px] tracking-widest transition-all ${patient.discharge ? 'bg-gray-600/20 text-gray-500 cursor-not-allowed border border-white/5' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg'}`}
             >
               {patient.discharge ? 'Already Discharged' : 'Check Discharge'}
             </button>
          )}
          {!isAdmin && patient.discharge && (
             <button onClick={onDischarge} className="hidden md:block px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold uppercase text-[10px] tracking-widest">
               View Discharge Report
             </button>
          )}
          <button onClick={logout} className="p-2 bg-white/5 rounded-xl hover:bg-white/10 transition-all">
            <LogOut size={20}/>
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-6 md:p-10 space-y-8 pb-20">
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* 1. PATIENT PROFILE CARD */}
            <section className="bg-[#1e293b] rounded-3xl p-8 border border-white/5 shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-xl font-bold flex items-center gap-3"><Users className="text-indigo-400"/> Patient Profile</h3>
                <span className={`px-3 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider border flex items-center gap-1.5 ${
                  (patient.discharge || patient.status === 'discharged')
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' 
                    : patient.status === 'critical'
                    ? 'bg-rose-500/15 border-rose-500/40 text-rose-400'
                    : 'bg-cyan-500/15 border-cyan-500/40 text-cyan-400'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${
                    (patient.discharge || patient.status === 'discharged')
                      ? 'bg-emerald-400'
                      : patient.status === 'critical'
                      ? 'bg-rose-400 animate-ping'
                      : 'bg-cyan-400'
                  }`}/>
                  {(patient.discharge || patient.status === 'discharged') ? 'DISCHARGED' : (patient.status ? patient.status.toUpperCase() : 'ACTIVE')}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                <ProfileItem label="Patient Name" value={patient.name} />
                <ProfileItem label="Patient ID" value={patient.patient_id} />
                <ProfileItem label="Doctor" value={patient.doctor} />
                <ProfileItem label="Diagnosis" value={patient.disease} />
                <ProfileItem label="Ward / Bed" value={patient.bed_number} />
                <ProfileItem label="Admission" value={new Date(patient.admission_date).toLocaleDateString()} />
              </div>
            </section>

            {/* 2. LATEST VITALS CARD */}
            <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <VitalValueCard label="Heart Rate" value={latestVitals?.heart_rate || '--'} unit="bpm" icon={<Activity size={18}/>} color="indigo" />
              <VitalValueCard label="SpO2" value={latestVitals?.spo2 || '--'} unit="%" icon={<Thermometer size={18}/>} color="cyan" />
              <VitalValueCard label="Temperature" value={latestVitals?.temperature || '--'} unit="°C" icon={<Thermometer size={18}/>} color="rose" />
              <VitalValueCard label="Resp Rate" value={latestVitals?.resp_rate || '--'} unit="br" icon={<Activity size={18}/>} color="emerald" />
            </section>

            {/* 4. VITALS GRAPH */}
            <section className="bg-[#1e293b] rounded-3xl p-8 border border-white/5 relative shadow-xl">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                  <h3 className="text-xl font-bold flex items-center gap-3"><Activity size={24} className="text-indigo-400"/> Telemetry Dashboard</h3>
                  <p className="text-xs text-gray-400 mt-1">Real-time health indicators and OCR vital extraction</p>
                </div>
                {isAdmin && (
                  <form onSubmit={handleUploadVitals} className="flex items-center gap-2">
                    <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 px-5 py-2.5 rounded-2xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20">
                      <Upload size={14}/> {uploading ? 'Analyzing...' : 'Upload Snapshot'}
                      <input type="file" name="image" className="hidden" onChange={(e) => e.target.form.requestSubmit()} />
                    </label>
                  </form>
                )}
              </div>
              
              <div className="h-[350px]">
                {vitals.length > 0 ? (
                  <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#64748b' } } } }} />
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-600 italic">No telemetry data available</div>
                )}
              </div>
            </section>

            {/* 3. VITALS HISTORY SECTION */}
            <section className="space-y-4">
              <h3 className="text-xl font-bold flex items-center gap-3"><History className="text-purple-400"/> Vitals Logs</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {vitals.slice(0, 6).map((v, i) => (
                  <div key={i} className="bg-[#1e293b] p-5 rounded-2xl border border-white/5 shadow-md">
                    <p className="text-[10px] text-gray-500 font-bold mb-3">{new Date(v.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</p>
                    <div className="grid grid-cols-3 gap-2">
                       <div className="text-center">
                         <span className="block text-[8px] text-gray-500 uppercase font-bold">HR</span>
                         <span className="text-sm font-bold">{v.heart_rate}</span>
                       </div>
                       <div className="text-center">
                         <span className="block text-[8px] text-gray-500 uppercase font-bold">SpO2</span>
                         <span className="text-sm font-bold">{v.spo2}</span>
                       </div>
                       <div className="text-center">
                         <span className="block text-[8px] text-gray-500 uppercase font-bold">TEMP</span>
                         <span className="text-sm font-bold">{v.temperature}</span>
                       </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* RIGHT COLUMN */}
          <div className="lg:col-span-4 space-y-8">
            
            {/* 5. PRESCRIPTIONS CARD */}
            <section className="bg-[#1e293b] rounded-3xl p-7 border border-white/5 shadow-xl">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2"><Stethoscope size={16}/> PHARMACY DISPENSARY ({prescriptions.length})</h3>
                {isAdmin && <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest bg-indigo-500/5 px-3 py-1 rounded-full border border-indigo-500/10">Admin Access</span>}
              </div>
              
              {isAdmin && (
                <div className="mb-6 relative">
                  <form onSubmit={handleAssignMedicine} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="relative md:col-span-2">
                      <input
                        name="medicine_name"
                        value={medQuery}
                        onChange={(e) => setMedQuery(e.target.value)}
                        placeholder="Search Indian Medicines / Nicknames (e.g. cetirizine, dolo, pan)"
                        required
                        autoComplete="off"
                        className="w-full bg-[#0f172a] border border-white/10 rounded-xl p-3 text-xs focus:border-indigo-500 outline-none text-white placeholder-gray-500"
                      />
                      {medSuggestions.length > 0 && (
                        <div className="absolute left-0 right-0 top-full mt-1 bg-[#0f172a] border border-white/15 rounded-xl shadow-2xl z-50 overflow-hidden divide-y divide-white/5 max-h-56 overflow-y-auto">
                          {medSuggestions.map((item, idx) => {
                            const isCrit = item.quantity < 50;
                            const isLow = item.quantity <= 100;
                            return (
                              <div
                                key={idx}
                                onClick={() => {
                                  setMedQuery(item.medicine_name);
                                  setSelectedMed(item);
                                  setMedSuggestions([]);
                                }}
                                className="p-2.5 hover:bg-white/5 cursor-pointer flex justify-between items-center text-xs transition-colors"
                              >
                                <div>
                                  <p className="font-bold text-white text-xs">{item.medicine_name}</p>
                                  <p className="text-[10px] text-gray-400">{item.generic_name || item.nickname || item.category}</p>
                                </div>
                                <div className="text-right">
                                  <span className="font-bold text-emerald-400 block">₹{item.price?.toFixed(2)}</span>
                                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                    isCrit ? 'bg-red-500/20 text-red-400 border border-red-500/30' : isLow ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400'
                                  }`}>
                                    {isCrit ? `🚨 Critical (${item.quantity})` : isLow ? `⚠️ Low (${item.quantity})` : `✓ In Stock (${item.quantity})`}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <input
                        name="quantity"
                        type="number"
                        min="1"
                        placeholder="Qty"
                        required
                        className="w-20 bg-[#0f172a] border border-white/10 rounded-xl p-3 text-xs focus:border-indigo-500 outline-none text-white text-center"
                      />
                      <button
                        type="submit"
                        disabled={prescribing}
                        className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all disabled:opacity-50 text-white"
                      >
                        {prescribing ? 'Checking...' : 'Assign'}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              <div className="space-y-3">
                {prescriptions.map((m, i) => {
                  const stock = m.stock_remaining;
                  const isCritical = (stock !== undefined && stock < 50) || m.warning_level === 'red';
                  const isLow = (stock !== undefined && stock <= 100) || m.warning_level === 'yellow';

                  return (
                    <div key={i} className="p-4 bg-[#0f172a]/70 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all space-y-2.5">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-white text-sm">{m.medicine_name}</h4>
                          <span className="text-[10px] text-gray-400">{m.generic_name || m.nickname || ''}</span>
                        </div>
                        <div className="text-right flex flex-col items-end">
                           <div className="flex items-center gap-2">
                              {isAdmin && (
                                <button onClick={() => handleDeleteMedicine(m._id)} className="p-1 hover:text-rose-500 transition-colors" title="Delete prescription">
                                  <Trash2 size={13}/>
                                </button>
                              )}
                              <span className="text-xs font-black text-indigo-400 block tracking-wider">₹{Number(m.total_cost || 0).toLocaleString()}</span>
                           </div>
                           <span className="text-[8px] text-gray-500 font-bold uppercase tracking-tighter">Total Cost</span>
                        </div>
                      </div>

                      <div className="flex justify-between items-center border-t border-white/5 pt-2 text-xs">
                        <div className="flex gap-4">
                          <div className="space-y-0.5">
                            <p className="text-[8px] text-gray-500 font-black uppercase">Prescribed Qty</p>
                            <p className="text-[11px] text-white font-bold">{m.quantity} Units</p>
                          </div>
                          <div className="space-y-0.5">
                            <p className="text-[8px] text-gray-500 font-black uppercase">Unit Price</p>
                            <p className="text-[11px] text-emerald-400 font-bold">₹{Number(m.price || 0).toFixed(2)}</p>
                          </div>
                        </div>
                        <span className="text-[9px] px-2 py-0.5 bg-indigo-500/10 text-indigo-400 rounded-lg uppercase font-black border border-indigo-500/10">
                          {m.status || 'Assigned'}
                        </span>
                      </div>

                      {/* Real-time stock availability with Yellow/Red warning */}
                      {stock !== undefined && (
                        <div className="pt-2 border-t border-white/5">
                          {isCritical ? (
                            <div className="flex items-center justify-between p-2 rounded-xl bg-red-500/15 border border-red-500/30">
                              <span className="text-[10px] font-bold text-red-400 flex items-center gap-1.5">
                                🚨 Critical Stock Alert: {stock} units left (&lt; 50)
                              </span>
                              <span className="text-[8px] font-black uppercase tracking-wider text-red-300 bg-red-500/30 px-2 py-0.5 rounded">
                                CRITICAL
                              </span>
                            </div>
                          ) : isLow ? (
                            <div className="flex items-center justify-between p-2 rounded-xl bg-amber-500/15 border border-amber-500/30">
                              <span className="text-[10px] font-bold text-amber-300 flex items-center gap-1.5">
                                ⚠️ Low Stock Warning: {stock} units left (≤ 100)
                              </span>
                              <span className="text-[8px] font-black uppercase tracking-wider text-amber-200 bg-amber-500/30 px-2 py-0.5 rounded">
                                LOW STOCK
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center justify-between p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                              <span className="text-[10px] font-bold text-emerald-400 flex items-center gap-1.5">
                                ✓ Available in Stock: {stock} units
                              </span>
                              <span className="text-[8px] font-black uppercase tracking-wider text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded">
                                IN STOCK
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
                {prescriptions.length === 0 && <p className="text-xs text-gray-500 italic py-4 text-center">No medications assigned</p>}
              </div>
            </section>

            {/* 6. BILLING SUMMARY CARD */}
            <section className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-3xl p-7 border border-white/5 shadow-xl">
              <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-widest mb-6 flex items-center gap-2"><CreditCard size={16}/> Billing Summary</h3>
              <div className="space-y-4">
                <div className="space-y-4 text-[11px]">
                  <div className="flex justify-between text-gray-400 items-center">
                    <span>Medicine Fees</span>
                    <span className="text-white font-bold">₹{Number(billing?.medicine_cost || 0).toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between text-gray-400 items-center">
                    <div className="flex items-center gap-2">
                       <span>Bed / Facility</span>
                       {isAdmin && (
                         <button onClick={() => handleUpdateCost('bed_cost_per_day', 'Bed Rate')} className="text-[9px] text-indigo-400 hover:text-indigo-300 font-bold uppercase underline">Update</button>
                       )}
                    </div>
                    <div className="text-right">
                       <span className="text-white font-bold block">₹{Number(billing?.bed_cost || 0).toLocaleString()}</span>
                       <span className="text-[8px] text-gray-500 italic">{billing?.bed_days || 1} days @ ₹{billing?.bed_rate || 500}/day</span>
                    </div>
                  </div>

                  <div className="flex justify-between text-gray-400 items-center">
                    <div className="flex items-center gap-2">
                       <span>Treatment</span>
                       {isAdmin && (
                         <button onClick={() => handleUpdateCost('treatment_cost', 'Treatment')} className="text-[9px] text-indigo-400 hover:text-indigo-300 font-bold uppercase underline">Update</button>
                       )}
                    </div>
                    <span className="text-white font-bold">₹{Number(billing?.treatment_cost || 0).toLocaleString()}</span>
                  </div>

                  {/* Manual Insurance Coverage Option (No default mock value, manually editable) */}
                  <div className="flex justify-between text-gray-400 items-center pt-1 border-t border-white/5">
                    <div className="flex items-center gap-2">
                       <span>Insurance Coverage</span>
                       {isAdmin && (
                         <button onClick={() => handleUpdateCost('insurance_coverage', 'Insurance Coverage')} className="text-[9px] text-indigo-400 hover:text-indigo-300 font-bold uppercase underline">Update</button>
                       )}
                    </div>
                    <span className={`font-bold ${billing?.insurance_coverage > 0 ? 'text-emerald-400' : 'text-gray-400'}`}>
                      {billing?.insurance_coverage > 0 ? `- ₹${Number(billing.insurance_coverage).toLocaleString()}` : '₹0'}
                    </span>
                  </div>
                </div>
                
                <div className="border-t border-white/10 pt-4 flex justify-between items-end">
                  <span className="text-[9px] text-gray-400 font-black uppercase tracking-widest">Total Bill:</span>
                  <span className="text-2xl font-black text-white">₹{Number(billing?.total_bill || 0).toLocaleString()}</span>
                </div>

                {billing?.paid_amount > 0 && (
                  <div className="flex justify-between text-[10px] text-cyan-400 font-bold px-1">
                    <span>Paid Amount</span>
                    <span>- ₹{Number(billing.paid_amount).toLocaleString()}</span>
                  </div>
                )}

                <div className="p-4 bg-indigo-500/10 rounded-2xl flex flex-col items-center justify-center border border-indigo-500/20">
                  <span className="text-[9px] font-black uppercase text-indigo-400 mb-1">Balance Remaining</span>
                  <span className="text-3xl font-black text-white">₹{Number(billing?.remaining_balance || 0).toLocaleString()}</span>
                </div>
              </div>
            </section>

            {/* 7. PAYMENT HISTORY CARD */}
            <section className="bg-[#1e293b] rounded-3xl p-7 border border-white/5 shadow-xl flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2"><History size={16}/> Payment History</h3>
                {isAdmin && (
                  <button onClick={() => setShowPayForm(!showPayForm)} className={`p-2 rounded-xl transition-all ${showPayForm ? 'bg-rose-500/10 text-rose-500' : 'bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white'}`}>
                    {showPayForm ? <X size={16}/> : <PlusCircle size={16}/>}
                  </button>
                )}
              </div>

              {isAdmin && showPayForm && (
                <motion.form initial={{height: 0, opacity: 0}} animate={{height: 'auto', opacity: 1}} onSubmit={handlePayment} className="mb-6 space-y-3 bg-[#0f172a] p-4 rounded-2xl border border-white/5">
                  <input name="amount" type="number" placeholder="Amount ₹" required className="w-full bg-transparent border-b border-white/10 p-2 text-xs focus:border-indigo-500 outline-none" />
                  <input name="purpose" placeholder="Purpose" required className="w-full bg-transparent border-b border-white/10 p-2 text-xs focus:border-indigo-500 outline-none" />
                  <button className="w-full bg-indigo-600 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500">Record</button>
                </motion.form>
              )}

              <div className="space-y-3 max-h-[250px] overflow-y-auto pr-1">
                {payments.map((p, i) => (
                  <div key={i} className="flex justify-between items-center p-3 bg-[#0f172a]/40 rounded-xl border border-white/5">
                    <div>
                      <p className="font-bold text-xs">₹{p.amount.toLocaleString()}</p>
                      <p className="text-[9px] text-gray-500 italic mt-0.5">{p.purpose}</p>
                    </div>
                    <span className="text-[8px] text-gray-600 font-bold">{new Date(p.timestamp).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            </section>

            {/* 8. ALERT HISTORY CARD */}
            <section className="bg-[#1e293b] rounded-3xl p-7 border border-white/5 shadow-xl">
              <h3 className="text-sm fon
              t-bold text-rose-400 uppercase tracking-widest mb-6 flex items-center gap-2"><ShieldAlert size={16}/> Risk Alerts</h3>
              <div className="space-y-3">
                {alerts.slice(0, 4).map((a, i) => (
                  <div key={i} className="p-4 bg-rose-500/5 rounded-2xl border border-rose-500/10 flex gap-4 items-center">
                    <AlertTriangle size={18} className="text-rose-500 flex-shrink-0" />
                    <div>
                      <p className="text-[10px] font-bold text-rose-200 uppercase leading-none mb-1">{a.message}</p>
                      <p className="text-[8px] text-gray-600">{new Date(a.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

          </div>
        </div>
      </main>
    </div>
  );
}

function ProfileItem({ label, value }) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{label}</p>
      <p className="text-sm font-bold text-white truncate">{value || '--'}</p>
    </div>
  );
}

function VitalValueCard({ label, value, unit, icon, color }) {
  const themes = {
    indigo: "bg-indigo-500/10 text-indigo-400 border-indigo-500/10",
    cyan: "bg-cyan-500/10 text-cyan-400 border-cyan-500/10",
    rose: "bg-rose-500/10 text-rose-400 border-rose-500/10",
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/10",
  };
  return (
    <div className={`p-5 rounded-3xl border ${themes[color]} group hover:bg-opacity-20 transition-all`}>
      <div className="flex justify-between items-start mb-3">
        {icon}
        <span className="text-[8px] font-black uppercase opacity-40">{unit}</span>
      </div>
      <p className="text-[9px] font-black uppercase tracking-widest mb-1 opacity-60">{label}</p>
      <div className="text-2xl font-black italic">{value}</div>
    </div>
  );
}

function VitalCard({ icon, label, value, unit, color }) {
  const themes = {
    indigo: "text-indigo-400 bg-indigo-500/10",
    cyan: "text-cyan-400 bg-cyan-500/10",
    rose: "text-rose-400 bg-rose-500/10",
    emerald: "text-emerald-400 bg-emerald-500/10",
  };
  return (
    <div className="bg-[#1e293b] p-6 rounded-3xl border border-white/5 hover:border-indigo-500/20 transition-all group">
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-all group-hover:scale-110 ${themes[color]}`}>{icon}</div>
      <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold italic tracking-tight">{value}</span>
        <span className="text-[10px] font-bold text-gray-500 uppercase">{unit}</span>
      </div>
    </div>
  );
}

function DischargePage({ patient_id, role, goBack }) {
  const [data, setData] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const isAdmin = role === 'admin';

  useEffect(() => {
    axios.get(`${API_BASE}/discharge_report/${patient_id}`)
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, [patient_id]);

  if (!data) return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
      <div className="text-center">
        <Activity className="animate-spin text-indigo-500 mb-4 mx-auto" size={48} />
        <p className="text-gray-400 italic">Generating Discharge Report...</p>
      </div>
    </div>
  );

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await axios.post(`${API_BASE}/generate_report/${patient_id}`);
      window.open(`${API_BASE}${res.data.file_url}`, '_blank');
    } catch (err) {
      alert("Error generating PDF: " + (err.response?.data?.detail || err.message));
    }
    setDownloading(false);
  };

  const isDischarged = data.patient?.discharge === true;
  const decisionDecision = data.decision?.discharge === true;
  const isReady = isDischarged || decisionDecision;

  return (
    <div className="min-h-screen bg-[#0f172a] text-white p-6 md:p-10 space-y-8 pb-20">
      {/* Top Banner */}
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-[#1e293b] p-6 rounded-3xl border border-white/5 shadow-xl">
        <div>
          <button onClick={goBack} className="text-gray-400 hover:text-white mb-4 text-xs font-bold uppercase tracking-widest">
            ← Back to Patient
          </button>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <CheckCircle2 className="text-emerald-400"/> Discharge Summary
          </h1>
          <p className="text-gray-400 mt-2">Patient ID: {patient_id} | Name: {data.patient?.name}</p>
        </div>
        <div className="flex gap-4 items-center">
            {isDischarged ? (
                <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl font-bold flex flex-col items-center">
                   <span className="uppercase text-[10px] tracking-widest">Already Discharged</span>
                   <span className="text-xs">{data.patient?.discharged_at ? new Date(data.patient.discharged_at).toLocaleString() : ''}</span>
                </div>
            ) : isReady ? (
                <span className="px-4 py-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl font-bold uppercase text-xs tracking-widest">
                  ✅ Ready for Discharge
                </span>
            ) : (
                <div className="px-4 py-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl max-w-xs">
                  <span className="font-bold uppercase text-[10px] tracking-widest block mb-1">❌ Not Ready</span>
                  <span className="text-xs italic">{data.decision?.reason || 'Criteria not met'}</span>
                </div>
            )}
            
            {isAdmin && isReady && (
                <button
                  onClick={handleDownload}
                  disabled={downloading}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold px-6 py-3 rounded-xl uppercase text-xs tracking-widest flex items-center gap-2"
                >
                  <Activity size={16} /> {downloading ? 'Generating...' : 'Download PDF'}
                </button>
            )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Patient Profile Snapshot */}
        <div className="bg-[#1e293b] rounded-3xl p-6 border border-white/5">
           <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2 mb-4"><Users size={16}/> Profile Snapshot</h3>
           <div className="space-y-4">
              <ProfileItem label="Diagnosis" value={data.patient?.disease} />
              <ProfileItem label="Doctor Notes" value={data.patient?.doctor_notes || 'No notes provided.'} />
              <ProfileItem label="Admission Date" value={data.patient?.admission_date ? new Date(data.patient.admission_date).toLocaleDateString() : 'N/A'} />
           </div>
        </div>
        
        {/* Billing Overview */}
        <div className="bg-[#1e293b] rounded-3xl p-6 border border-white/5">
           <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2 mb-4"><CreditCard size={16}/> Financial Settlment</h3>
           <div className="space-y-4 text-sm mt-6">
              <div className="flex justify-between">
                 <span className="text-gray-400">Total Bill</span>
                 <span className="font-bold text-white">₹{data.billing?.total_bill?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                 <span className="text-gray-400">Total Paid</span>
                 <span className="font-bold text-blue-400">₹{data.payments?.reduce((a, b) => a + b.amount, 0).toLocaleString()}</span>
              </div>
              <div className="border-t border-white/10 pt-4 flex justify-between">
                 <span className="font-bold text-gray-400 uppercase text-xs tracking-widest">Balance</span>
                 <span className="font-black text-white text-lg">₹{data.billing?.remaining_balance?.toLocaleString()}</span>
              </div>
           </div>
        </div>
      </div>
      
      {/* Vitals & Alerts Highlights */}
      <div className="max-w-4xl mx-auto space-y-6">
        <h3 className="text-lg font-bold flex items-center gap-2"><Thermometer/> Critical Highlights</h3>
        {data.alerts?.length > 0 && (
           <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl mb-4">
              <h4 className="text-rose-400 text-xs font-bold uppercase tracking-widest mb-2">Recent Alerts</h4>
              <ul className="list-disc pl-5 space-y-1">
                 {data.alerts.slice(0, 3).map((a, i) => (
                    <li key={i} className="text-xs text-rose-200">{a.message} <span className="text-gray-500">({new Date(a.timestamp).toLocaleDateString()})</span></li>
                 ))}
              </ul>
           </div>
        )}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           {data.vitals?.slice(0, 4).map((v, i) => (
             <div key={i} className="bg-[#1e293b] border border-white/5 p-4 rounded-xl text-center">
                 <span className="block text-[8px] text-gray-500 uppercase font-bold mb-2">{new Date(v.timestamp).toLocaleString([], {hour:'2-digit', minute:'2-digit', month: 'short', day: 'numeric'})}</span>
                 <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-400 block text-[8px] uppercase">HR</span>
                      <span className="font-bold">{v.heart_rate}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 block text-[8px] uppercase">SpO2</span>
                      <span className="font-bold">{v.spo2}%</span>
                    </div>
                 </div>
             </div>
           ))}
        </div>
      </div>
    </div>
  );
}

export default App;
