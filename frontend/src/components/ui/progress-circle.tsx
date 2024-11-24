import * as React from "react"
import { cn } from "@/utils/cn"

interface ProgressCircleProps extends React.SVGProps<SVGSVGElement> {
  value: number
  size?: number
  strokeWidth?: number
}

const ProgressCircle = React.forwardRef<SVGSVGElement, ProgressCircleProps>(
  ({ value, size = 120, strokeWidth = 8, className, ...props }, ref) => {
    const radius = (size - strokeWidth) / 2
    const circumference = radius * 2 * Math.PI
    const progress = value / 100
    const offset = circumference - progress * circumference

    return (
      <svg
        ref={ref}
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className={cn("transform -rotate-90", className)}
        {...props}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className="stroke-muted fill-none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="stroke-primary fill-none transition-all duration-500 ease-out"
          strokeLinecap="round"
        />
        {/* Text in the middle */}
        <text
          x="50%"
          y="50%"
          dy=".3em"
          textAnchor="middle"
          className="fill-primary text-lg font-medium transform rotate-90"
        >
          {`${Math.round(value)}%`}
        </text>
      </svg>
    )
  }
)
ProgressCircle.displayName = "ProgressCircle"

export { ProgressCircle }