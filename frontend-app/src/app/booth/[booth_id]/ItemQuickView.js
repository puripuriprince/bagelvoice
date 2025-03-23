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
import { Download, EyeIcon, TrashIcon } from "lucide-react";

export default function ItemQuickView({ source }) {
	function onDownloadSource() {
		console.log("Download source", source.id);
	}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem onSelect={e => e.preventDefault()}>
					<EyeIcon size={16} />
					Quick View
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Quick View</DialogTitle>
					<DialogDescription>{source.summary}</DialogDescription>
					<Button onClick={onDownloadSource}>
						<Download size={16} />
						Download Source
					</Button>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
