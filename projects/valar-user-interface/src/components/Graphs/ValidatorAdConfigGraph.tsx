import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Label } from "recharts";


export function ValidatorAdConfigGraph({
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
    <ChartContainer
      className="h-full max-h-52 w-full pr-12"
      config={chartConfig}
    >
      <LineChart accessibilityLayer data={chartData}>
        <XAxis
          dataKey={xKey}
          tickLine={false}
          axisLine={false}
          tickMargin={8}

        >
          <Label
            value="Stake (ALGO)"
            offset={-5}
            position="insideBottom"
          />
        </XAxis>
        <YAxis
          dataKey={yKey}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        >
          <Label
            value="Operational fee (per month)"
            angle={-90}
            position="insideBottomLeft"
            offset={20}
          />
        </ YAxis>
        <CartesianGrid
          vertical={true} 
          horizontal={true} 
        />
        <ChartTooltip
          // cursor={false}
          content={<ChartTooltipContent indicator="line" hideLabel />}
        />
        <Line
          dataKey={yKey}
          type="linear"
          stroke="var(--color-y)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
