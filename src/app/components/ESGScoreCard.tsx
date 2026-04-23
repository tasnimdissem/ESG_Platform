import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ESGScoreCardProps {
  title: string;
  score: number;
  previousScore: number;
  icon: React.ReactNode;
  color: string;
}

export function ESGScoreCard({ title, score, previousScore, icon, color }: ESGScoreCardProps) {
  const change = score - previousScore;
  const changePercent = ((change / previousScore) * 100).toFixed(1);

  const getTrendIcon = () => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendColor = () => {
    if (change > 0) return 'text-green-600 bg-green-50';
    if (change < 0) return 'text-red-600 bg-red-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center`}>
          {icon}
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${getTrendColor()}`}>
          {getTrendIcon()}
          <span className="text-xs font-semibold">{Math.abs(parseFloat(changePercent))}%</span>
        </div>
      </div>
      
      <h3 className="text-gray-600 text-sm font-medium mb-2">{title}</h3>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold">{score}</span>
        <span className="text-gray-400 text-sm">/100</span>
      </div>
      
      <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
