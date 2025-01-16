import ColumnDropdown from "@/components/DataTable/ColumnDropdown";
import TableMain from "@/components/DataTable/TableMain";
import TablePagination from "@/components/DataTable/TablePagination";
import TableSearch from "@/components/DataTable/TableSearch";
import IdenticonAvatar from "@/components/Identicon/Identicon";
import ITooltip from "@/components/Tooltip/ITooltip";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { StakeReqs } from "@/lib/types";
import {
  ColumnFiltersState,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useState } from "react";

import StakeListMobile from "./StakeListMobile";
import { ToolTips } from "@/constants/tooltips";
import { StakeListItem, getStakeList } from "./utils";
import useUserStore from "@/store/userStore";
import AdStatus from "@/components/Status/AdStatus";
import DelCoDrawer from "@/components/Drawers/DelCoDrawer/DelCoDrawer";
import { ellipseAddress } from "@/utils/convert";

const columnHelper = createColumnHelper<StakeListItem>();

function StakeListCard({
  stakeReqs,
}:{
  stakeReqs: StakeReqs;
}) {
  const { valAdsMap } = useAppGlobalState();
  const { user } = useUserStore();

  const [stakeList, setStakeList] = useState<StakeListItem[]>([]);
  const [tableData, setTableData] = useState<StakeListItem[]>([]);

  const [showAll, setShowAll] = useState(false);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  // Convert Validator Ads to table items
  useEffect(() => {
    const fetch = async () => {
      if (!valAdsMap) return;
      const stakeList = await getStakeList(valAdsMap, stakeReqs, user);
      setStakeList(stakeList);
      console.log("Updating table data due to change in valAdsMap, stakeReqs, user", valAdsMap, stakeReqs, user);
    };

    fetch();
  }, [valAdsMap, stakeReqs, user]);

  // Filter table items based on show all
  useEffect(() => {
    const filteredStakeList = showAll ? stakeList : stakeList.filter((item) => item.canStake);
     setTableData(filteredStakeList);
  }, [stakeList, showAll]);

  // Define table columns
  const columns = [
    columnHelper.accessor("name", {
      header: "Node runner name",
      cell: (info) => (
        <div className="flex items-center gap-2">
          <IdenticonAvatar value={info.getValue() as string} />
          {ellipseAddress(info.getValue())}
        </div>
      ),
      enableHiding: false,
    }),
    columnHelper.accessor("adId", {header: "Ad ID"}),
    columnHelper.accessor("totalPrice", {header: "Total price"}),
    columnHelper.accessor("currency", {header: "Currency"}),
    columnHelper.accessor("occupation", {header: "Occupation"}),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => {
        const status = info.getValue();
        return <AdStatus status={status} />;
      },
    }),
    columnHelper.accessor("setupFee", {header: "Setup fee"}),
    columnHelper.accessor("opFee", {header: "Op. fee"}),
    columnHelper.accessor("opFeeMin", {header: "Op. fee min"}),
    columnHelper.accessor("opFeeVar", {header: "Op. fee var"}),
    columnHelper.accessor("setupTime", {header: "Setup time"}),
    columnHelper.accessor("confirmationTime", {header: "Confirmation time"}),
    columnHelper.accessor("minDuration", {header: "Min duration"}),
    columnHelper.accessor("maxDuration", {header: "Max duration"}),
    columnHelper.accessor("validUntil", {header: "Valid until"}),
    columnHelper.accessor("maxStake", {header: "Max stake"}),
    columnHelper.accessor("maxWarnings", {header: "Max warnings"}),
    columnHelper.accessor("gated", {header: "Gated"}),
    columnHelper.display({
      header: () => null,
      id: "stake",
      cell: (info) => <DelCoDrawer
        valAppId={info.row.getValue("adId")}
        stakeReqs={stakeReqs}
        possible={info.row.original.canStake}
      />,
      enableHiding: false,
    }),
  ];
  const columnVisibility = {
    currency: false,
    status: false,
    setupFee: false,
    opFee: false,
    opFeeMin: false,
    opFeeVar: false,
    setupTime: false,
    confirmationTime: false,
    minDuration: false,
    maxDuration: false,
    validUntil: false,
    maxStake: false,
    maxWarnings: false,
    gated: false,
  };

  // Define table
  const validatorTable = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),

    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,

    getFilteredRowModel: getFilteredRowModel(),
    onColumnFiltersChange: setColumnFilters,

    state: {
      pagination,
      columnFilters,
    },

    initialState: {
      columnVisibility: columnVisibility,
    },
  });

  return (
    <>
      <div className="rounded-md px-2 py-2 lg:bg-background-light">
        <div className="flex flex-col gap-2">
          <div className="flex flex-col justify-between gap-2 px-1 lg:flex-row lg:items-center">
            <h1 className="font-bold">Node Runners</h1>
            <div className="flex justify-between gap-1">
              <div className="flex w-[200px] items-center gap-2">
                <Checkbox
                  className="border-border"
                  checked={showAll}
                  onCheckedChange={(v) =>
                    setShowAll(v === "indeterminate" ? false : v)
                  }
                />
                <Label className="h-6 text-sm font-normal">
                  Show All{" "}
                  <ITooltip value={ToolTips.StakeShowAll} />
                </Label>
              </div>
              <TableSearch
                table={validatorTable}
                searchColumn="name"
                className="max-w-[150px]"
              />
              <ColumnDropdown
                className="hidden lg:block"
                table={validatorTable}
              />
            </div>
          </div>
          <Separator className="hidden bg-border lg:block" />
          <div className="flex flex-col items-end rounded-lg bg-background p-1 lg:bg-transparent">
            <div className="hidden w-full lg:block">
              <TableMain table={validatorTable} />
            </div>
            <div className="block w-full lg:hidden">
              <StakeListMobile table={validatorTable} />
            </div>
            <TablePagination table={validatorTable} pagination={pagination} />
          </div>
        </div>
      </div>
    </>
  );
}

export default StakeListCard;
