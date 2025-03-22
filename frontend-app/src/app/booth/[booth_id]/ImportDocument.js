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

export default function ImportDocument() {
	const [files, setFiles] = useState([]);

	// TODO: Upload the files
	function handleUpload() {
		console.log(files);
	}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem onSelect={e => e.preventDefault()}>
					<DocumentIcon className="w-4 h-4" />
					From Document (.pdf, .docx, ...)
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Import a Document</DialogTitle>
					<DialogDescription>
						Select the file(s) you want to import
					</DialogDescription>
					<Input
						type="file"
						multiple
						onChange={e => setFiles(e.target.files)}
					/>
					<Button onClick={handleUpload}>Upload</Button>
					<DialogFooter></DialogFooter>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
