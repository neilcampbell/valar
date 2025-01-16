

const LinkExt: React.FC<{
  href: string
  text: string
  className?: string
}> = ({
  href,
  text,
  className,
}) => {

  return (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer" 
      className={className}
    >
      {text}
    </a>
  );
}
export default LinkExt;
