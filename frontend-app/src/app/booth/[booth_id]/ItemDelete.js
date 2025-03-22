import { DocumentIcon } from "@heroicons/react/24/outline";
import {
	Dialog,
	DialogTrigger,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogDescription,
	DialogFooter,
	DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { DropdownMenuItem } from "@radix-ui/react-dropdown-menu";
import useSourcesStore from "@/stores/useSourcesStore";
import { TrashIcon } from "lucide-react";

export default function ItemDelete({ source }) {
	const deleteSource = useSourcesStore(state => state.deleteSource);
	function handleDelete() {
		deleteSource(source.id);
	}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem
					className={"text-red-500 font-semibold"}
					onSelect={e => e.preventDefault()}
				>
					<TrashIcon size={16} className="text-red-500" />
					Delete
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Delete Source</DialogTitle>
					<DialogDescription>
						Are you sure you want to delete this source?
					</DialogDescription>
					<DialogFooter className={"grid grid-cols-1 xl:grid-cols-2"}>
						<DialogClose asChild>
							<Button variant="outline">No, cancel</Button>
						</DialogClose>

						<DialogClose asChild>
							<Button
								onClick={handleDelete}
								variant="destructive"
							>
								Yes, delete
							</Button>
						</DialogClose>
					</DialogFooter>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
