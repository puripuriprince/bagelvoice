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

export default function ImportDocument() {
	const [files, setFiles] = useState([]);
	const [isLoading, setIsLoading] = useState(false);

	// TODO: Upload the files
	function handleUpload() {
		if (!files || files.length === 0) {
		  console.error('No files selected');
		  return;
		}
		
		setIsLoading(true);
		
		const formData = new FormData();
		Array.from(files).forEach((file, index) => {
		  formData.append(`file`, file);
		});
		
		fetch('http://127.0.0.1:5000/api/upload', {
		  method: 'POST',
		  body: formData,
		})
		  .then(response => {
			if (!response.ok) {
			  throw new Error(`Upload failed with status: ${response.status}`);
			}
			return response.json();
		  })
		  .then(data => {
			console.log('Upload successful:', data);
			// Show success toast
			// Close dialog
			setFiles([]);
		  })
		  .catch(error => {
			console.error('Error uploading files:', error);
			// Show error toast
		  })
		  .finally(() => {
			setIsLoading(false);
		  });

		  setTimeout(() => {
			for (const file of files) {
				addSource({
					name: file.name,
					summary: "this is a file that was uploaded",
				});
			}
		}, 2000);
	  }
	// 	if (files.length === 0) {
	// 		alert("Please select files first");
	// 		return;
	// 	}

	// 	const formData = new FormData();

	// 	// Append all files to the FormData object
	// 	for (const file of files) {
	// 		formData.append("files", file);
	// 	}

	// 	// Show loading state (if you have one)
	// 	// setIsLoading(true);

	// 	// Make the request to your backend
	// 	fetch(process.env.NEXT_PUBLIC_API_URL + "/summarize", {
	// 		method: "POST",
	// 		body: formData,
	// 		// No need to set Content-Type header, it's automatically set with boundary for FormData
	// 	})
	// 		.then(response => {
	// 			if (!response.ok) {
	// 				throw new Error(`HTTP error! Status: ${response.status}`);
	// 			}
	// 			return response.json();
	// 		})
	// 		.then(data => {
	// 			// Process the response and add each file to your sources
	// 			data.results.forEach(result => {
	// 				addSource({
	// 					id: result.id,
	// 					name: result.filename,
	// 					summary:
	// 						result.summary ||
	// 						result.error ||
	// 						"Failed to generate summary",
	// 				});
	// 			});

	// 			// Clear the files state if you want to reset the file input
	// 			setFiles([]);

	// 			// Display success message
	// 			alert(`Successfully processed ${data.results.length} files`);
	// 		})
	// 		.catch(error => {
	// 			console.error("Error uploading files:", error);
	// 			alert("Failed to upload files. See console for details.");
	// 		});
	// 	// .finally(() => {
	// 	//   setIsLoading(false);
	// 	// });
	// }

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
					<DialogClose asChild>
						<Button onClick={handleUpload}>Upload</Button>
					</DialogClose>
					<DialogFooter></DialogFooter>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
