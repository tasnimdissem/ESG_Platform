import { ESGScoreCard } from '../components/ESGScoreCard';
import { Leaf, Droplet, Users, TrendingUp, Award, AlertCircle } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const historicalData = [
  { month: 'Jan', Environmental: 72, Social: 68, Governance: 75, overall: 71.7 },
  { month: 'Fév', Environmental: 74, Social: 70, Governance: 76, overall: 73.3 },
  { month: 'Mar', Environmental: 76, Social: 72, Governance: 78, overall: 75.3 },
  { month: 'Avr', Environmental: 78, Social: 74, Governance: 80, overall: 77.3 },
  { month: 'Mai', Environmental: 80, Social: 76, Governance: 82, overall: 79.3 },
  { month: 'Jun', Environmental: 82, Social: 78, Governance: 84, overall: 81.3 },
];

const predictionData = [
  { month: 'Jun', actual: 81.3, predicted: 81.3 },
  { month: 'Jul', predicted: 83.5 },
  { month: 'Aoû', predicted: 85.2 },
  { month: 'Sep', predicted: 86.8 },
  { month: 'Oct', predicted: 88.1 },
  { month: 'Nov', predicted: 89.4 },
  { month: 'Déc', predicted: 90.2 },
];

const sectorComparison = [
  { sector: 'Technologie', score: 85 },
  { sector: 'Finance', score: 78 },
  { sector: 'Énergie', score: 65 },
  { sector: 'Santé', score: 82 },
  { sector: 'Votre entreprise', score: 81 },
];

const riskData = [
  { name: 'Émissions CO2', current: 75, target: 90 },
  { name: 'Diversité', current: 82, target: 85 },
  { name: 'Gouvernance', current: 84, target: 88 },
  { name: 'Éthique', current: 88, target: 90 },
  { name: 'Transparence', current: 80, target: 92 },
];

const performanceDistribution = [
  { name: 'Excellent (80-100)', value: 35, color: '#10b981' },
  { name: 'Bon (60-79)', value: 45, color: '#3b82f6' },
  { name: 'Moyen (40-59)', value: 15, color: '#f59e0b' },
  { name: 'Faible (0-39)', value: 5, color: '#ef4444' },
];

export default function Dashboard() {
  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard ESG</h1>
        <p className="text-gray-600">Vue d'ensemble et prédictions ML de vos scores ESG</p>
      </div>

      {/* ESG Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ESGScoreCard
          title="Score Global ESG"
          score={81}
          previousScore={75}
          icon={<Award className="w-6 h-6 text-emerald-700" />}
          color="bg-emerald-100"
        />
        <ESGScoreCard
          title="Environnemental"
          score={82}
          previousScore={76}
          icon={<Leaf className="w-6 h-6 text-green-700" />}
          color="bg-green-100"
        />
        <ESGScoreCard
          title="Social"
          score={78}
          previousScore={72}
          icon={<Users className="w-6 h-6 text-blue-700" />}
          color="bg-blue-100"
        />
        <ESGScoreCard
          title="Gouvernance"
          score={84}
          previousScore={78}
          icon={<Droplet className="w-6 h-6 text-purple-700" />}
          color="bg-purple-100"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Historical Trends */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg">Tendances Historiques</h3>
            <div className="flex items-center gap-2 text-sm text-green-600">
              <TrendingUp className="w-4 h-4" />
              <span className="font-semibold">+12.8%</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="Environmental" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
              <Area type="monotone" dataKey="Social" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
              <Area type="monotone" dataKey="Governance" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* ML Prediction */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-lg">Prédiction ML (6 mois)</h3>
              <p className="text-sm text-gray-500">Basé sur l'algorithme Random Forest</p>
            </div>
            <div className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
              Précision: 94.2%
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={predictionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" domain={[75, 95]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={2} dot={{ r: 5 }} name="Score Actuel" />
              <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 5 }} name="Prédiction" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sector Comparison */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="font-bold text-lg mb-4">Comparaison Sectorielle</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sectorComparison} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" stroke="#6b7280" domain={[0, 100]} />
              <YAxis dataKey="sector" type="category" stroke="#6b7280" width={120} />
              <Tooltip />
              <Bar dataKey="score" fill="#10b981" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radar Chart */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="font-bold text-lg mb-4">Analyse des Risques</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={riskData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="name" stroke="#6b7280" />
              <PolarRadiusAxis stroke="#6b7280" domain={[0, 100]} />
              <Radar name="Actuel" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
              <Radar name="Objectif" dataKey="target" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Distribution Pie */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="font-bold text-lg mb-4">Distribution Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={performanceDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {performanceDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts Section */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-orange-500" />
          Alertes et Actions Recommandées
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Émissions Carbone</h4>
                <p className="text-xs text-gray-600">Réduction de 15% nécessaire pour atteindre l'objectif 2027</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Diversité & Inclusion</h4>
                <p className="text-xs text-gray-600">Score en amélioration - continuer les initiatives actuelles</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Award className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Gouvernance</h4>
                <p className="text-xs text-gray-600">Excellente performance - maintenir les standards</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
