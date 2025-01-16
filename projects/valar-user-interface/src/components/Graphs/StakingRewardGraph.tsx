import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Line, LineChart, XAxis, YAxis } from "recharts";

export function StakingRewardGraph({
  chartData,
  xKey,
  yKey,
  chartConfig,
}: {
  chartData: any[];
  xKey: string;
  yKey: string;
  chartConfig: ChartConfig;
}) {
  return (
    <ChartContainer className="pr-12" config={chartConfig}>
      <LineChart accessibilityLayer data={chartData}>
        <XAxis
          dataKey={xKey}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(value) => {
            if (xKey === "month" || xKey === "day") {
              return value.slice(0, 3);
            } else if (xKey === "date") {
              return value.slice(0, 2);
            } else {
              return value;
            }
          }}
        />
        <YAxis
          dataKey={yKey}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent className="text-black" />}
        />
        <Line
          dataKey={yKey}
          type="linear"
          stroke="var(--color-price)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
