export default function ScoreCircle({ score, size = 120, strokeWidth = 8, label = 'Score' }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 90) return '#00ff88';
    if (s >= 70) return '#00d4ff';
    if (s >= 50) return '#f59e0b';
    if (s >= 30) return '#f97316';
    return '#ef4444';
  };

  const getGrade = (s) => {
    if (s >= 90) return 'Excellent';
    if (s >= 70) return 'Good';
    if (s >= 50) return 'Fair';
    if (s >= 30) return 'Poor';
    return 'Damaged';
  };

  const color = getColor(score);

  return (
    <div className="score-circle" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1.5s ease-in-out',
            filter: `drop-shadow(0 0 6px ${color}40)`
          }}
        />
      </svg>
      <div className="text-center">
        <div className="text-2xl font-bold" style={{ color }}>{score}</div>
        <div className="text-[10px] uppercase tracking-wider text-gray-500">{label}</div>
        <div className="text-xs font-semibold mt-0.5" style={{ color }}>{getGrade(score)}</div>
      </div>
    </div>
  );
}
