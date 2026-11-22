import ArticlesTable from "@/components/admin/ArticlesTable";

export default function AdminArticlesPage() {
  return (
    <ArticlesTable
      title="إدارة الأخبار"
      emptyMessage="لا توجد أخبار مجمّعة بعد. شغّل التوريد من النظرة العامة."
    />
  );
}
