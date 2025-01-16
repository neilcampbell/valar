import * as React from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
} from "@/components/ui/popover";


export function DatePicker({
  open,
  onOpenChange,
  date,
  setDate,
}: {
  open: boolean;
  onOpenChange: () => void;
  date: Date | undefined;
  setDate: React.Dispatch<React.SetStateAction<Date | undefined>>;
}) {
 
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={date}
          onSelect={setDate}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );
}
