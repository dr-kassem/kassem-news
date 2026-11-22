import ArticlesTable from "@/components/admin/ArticlesTable";

export default function ReviewQueuePage() {
  return (
    <ArticlesTable
      status="review"
      title="قائمة المراجعة"
      emptyMessage="لا توجد أخبار بانتظار المراجعة حالياً."
    />
  );
}
