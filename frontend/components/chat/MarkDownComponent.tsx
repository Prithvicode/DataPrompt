// components/MarkdownComponents.tsx
import React from "react";

const markdownComponents = {
  table({ children, ...props }: any) {
    return (
      <table
        className="table-auto border-collapse border border-gray-400 my-4"
        {...props}
      >
        {children}
      </table>
    );
  },
  thead({ children, ...props }: any) {
    return (
      <thead className="bg-gray-100" {...props}>
        {children}
      </thead>
    );
  },
  tbody({ children, ...props }: any) {
    return <tbody {...props}>{children}</tbody>;
  },
  tr({ children, ...props }: any) {
    return (
      <tr className="border-b border-gray-300" {...props}>
        {children}
      </tr>
    );
  },
  th({ children, ...props }: any) {
    return (
      <th className="border px-3 py-1 font-semibold text-left" {...props}>
        {children}
      </th>
    );
  },
  td({ children, ...props }: any) {
    return (
      <td className="border px-3 py-1" {...props}>
        {children}
      </td>
    );
  },
  code({ node, inline, className, children, ...props }: any) {
    if (inline) {
      return (
        <code className="bg-gray-300 px-1 rounded" {...props}>
          {children}
        </code>
      );
    }
    return (
      <pre className="bg-gray-800 text-gray-100 p-2 rounded-md overflow-x-auto text-sm">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
  a({ node, children, ...props }: any) {
    return (
      <a className="text-blue-600 hover:underline" {...props}>
        {children}
      </a>
    );
  },
  ul({ node, children, ...props }: any) {
    return (
      <ul className="list-disc pl-4 space-y-1" {...props}>
        {children}
      </ul>
    );
  },
  ol({ node, children, ...props }: any) {
    return (
      <ol className="list-decimal pl-4 space-y-1" {...props}>
        {children}
      </ol>
    );
  },
  h1({ node, children, ...props }: any) {
    return (
      <h1 className="text-2xl font-bold mt-4 mb-2" {...props}>
        {children}
      </h1>
    );
  },
  h2({ node, children, ...props }: any) {
    return (
      <h2 className="text-xl font-semibold mt-3 mb-1.5" {...props}>
        {children}
      </h2>
    );
  },
  blockquote({ node, children, ...props }: any) {
    return (
      <blockquote
        className="border-l-4 border-gray-400 pl-3 text-gray-600"
        {...props}
      >
        {children}
      </blockquote>
    );
  },
};

export default markdownComponents;
