import React from "react";

interface InfoCardProps {
  title: string;
  value: string;
  percentage?: string;
  color?: string; // Tailwind text color classes, e.g., "text-green-500"
}

const InfoCard: React.FC<InfoCardProps> = ({ title, value, percentage, color }) => {
  return (
    <div className="bg-background p-6 rounded-lg shadow-md w-full max-w-xs">
      <div className="flex flex-col gap-1">
        <h4 className="text-sm font-medium text-text-tertiary">{title}</h4>
        <div className="flex justify-between items-center mt-2">
          <span className="text-xl font-medium text-text">{value}</span>
          {percentage && (
            <span className={`text-sm font-medium ${color || "text-green-500"}`}>
              {percentage}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default InfoCard;
