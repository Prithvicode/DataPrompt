interface FileUploadProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}

export default function FileUpload({
  file,
  onFileChange,
  disabled = false,
}: FileUploadProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files ? e.target.files[0] : null;
    onFileChange(uploadedFile);
  };

  return (
    <div className="flex items-center space-x-4">
      <input
        type="file"
        onChange={handleFileChange}
        className="hidden"
        id="fileUpload"
        disabled={disabled}
      />
      <label
        htmlFor="fileUpload"
        className={`size-10 flex items-center justify-center rounded-full ${
          disabled ? "bg-[#444444]" : "bg-[#2A9FD6] hover:bg-[#1D8CB7]"
        } text-white cursor-pointer transition duration-300`}
      >
        <span className="text-3xl">+</span>
      </label>
      {file && (
        <span className="text-gray-300 text-sm truncate max-w-xs">
          {file.name}
        </span>
      )}
    </div>
  );
}
