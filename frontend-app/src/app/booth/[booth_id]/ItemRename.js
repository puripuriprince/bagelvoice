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
import { PencilIcon } from "lucide-react";
import useSourcesStore from "@/stores/useSourcesStore";

export default function ItemRename({ source }) {
	const [textInput, setTextInput] = useState("");
	const renameSource = useSourcesStore(state => state.renameSource);

	function handleRename() {
		if (!textInput) return;
		renameSource(source.id, textInput);
	}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem onSelect={e => e.preventDefault()}>
					<PencilIcon size={16} />
					Rename
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Rename Source</DialogTitle>
					<Input onChange={e => setTextInput(e.target.value)} />
					<DialogClose asChild>
						<Button onClick={handleRename}>Rename</Button>
					</DialogClose>
					<DialogFooter></DialogFooter>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
