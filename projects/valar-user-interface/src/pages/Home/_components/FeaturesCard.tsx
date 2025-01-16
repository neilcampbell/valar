const FeaturesCard = ({
  icon,
  head,
  desc,
}: {
  icon: JSX.Element;
  head: JSX.Element | string;
  desc: JSX.Element | string;
}) => {
  return (
    <div className="flex flex-col gap-1">
      {icon}
      <h1 className="text-base font-semibold leading-7 lg:text-lg lg:font-bold">
        {head}
      </h1>
      <p className="text-sm leading-5">{desc}</p>
    </div>
  );
};

export default FeaturesCard;
