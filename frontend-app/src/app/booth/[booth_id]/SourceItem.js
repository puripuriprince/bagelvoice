import { Checkbox } from "@/components/ui/checkbox";
import { EllipsisVertical, EyeIcon, PencilIcon, TrashIcon } from "lucide-react";
import useSourcesStore from "@/stores/useSourcesStore";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function SourceItem({ source }) {
	const setSourceChecked = useSourcesStore(state => state.setSourceChecked);

	function handleQuickView() {}
	function handleRename() {}
	function handleDelete() {}

	return (
		<div className="flex justify-between items-center">
			<div
				className="flex items-center gap-4 rounded-lg cursor-pointer hover:underline grow"
				onClick={setSourceChecked.bind(
					this,
					source.id,
					!source.selected,
				)}
			>
				<Checkbox checked={source.selected} />
				<h2 className="font-semibold">{source.name}</h2>
			</div>
			<DropdownMenu>
				<DropdownMenuTrigger>
					<EllipsisVertical className="w-6 h-6 text-white cursor-pointer hover:brightness-75 duration-100" />
				</DropdownMenuTrigger>

				<DropdownMenuContent>
					<DropdownMenuItem>
						<EyeIcon size={16} />
						Quick View
					</DropdownMenuItem>
					<DropdownMenuItem>
						<PencilIcon size={16} />
						Rename
					</DropdownMenuItem>
					<DropdownMenuItem className={"text-red-500 font-semibold"}>
						<TrashIcon size={16} className="text-red-500" />
						Delete
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</div>
	);
	//<div className="bg-white p-4 rounded-lg shadow-md">
	//	<h2 className="text-lg font-semibold">{source.name}</h2>
	//</div>
}
